# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 16:22:54 2022

Script #4 qui détermine toutes les infos du vol (aéroports départs et arrivés, temps de vol, CO2 émis, etc).

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import math
import numpy as np
import os

#other script
from src.core import maths_for_map


#%% load df_airport
path = os.getcwd()

path_airports = os.path.join(path, "input", "airports.csv")

#%% on charge le df_airport
df_airports = pd.read_csv(path_airports, delimiter = ",", usecols=['ident', 'name', 'latitude_deg', "longitude_deg"])
df_airports = df_airports.rename(columns={"ident" : "airport_icao"})


#%%
def fct_get_data_from_csv(csv, regis, icao, co2):

    df_csv = pd.read_csv(csv)

    #pour enregistrer seulement le chemin relatif dans le csv final (pour github notamment)
    csv_relatif = os.path.relpath(csv, path)

    #to remove NaN/Nat dans la colonne time du csv
    df_csv = df_csv.dropna()
    df_csv["time"] = pd.to_datetime(df_csv["time"], errors='coerce')
    df_csv = df_csv[pd.notnull(df_csv["time"])]

    # on récupère la position initiale de l'avion
    lat_ini = df_csv["lat"].iloc[0]
    long_ini = df_csv["long"].iloc[0]
    time_ini = df_csv["time"].iloc[0]
    elev_ini = df_csv["elevation"].iloc[0:3].mean()#pour eviter pics étranges au départ

    # on récupère la position finale de l'avion
    lat_last = df_csv["lat"].iloc[-1]
    long_last = df_csv["long"].iloc[-1]
    time_last = df_csv["time"].iloc[-1]
    elev_last = df_csv["elevation"].iloc[-3:-1].mean()#pour eviter pics étranges à l'arrivée

    # on créer une variable de date pour future utilisation dans "e_csv_to_map.py"
    dep_date_only_utc = str(time_ini.date())
    dep_date_utc = str(time_ini)
    arr_date_utc = str(time_last)

    # on calcule la variable importante du temps de vol
    flt_duration_min = round((time_last - time_ini).seconds/60.0,2)

    # on calcule la variable importante du co2
    flt_co2 = round(co2/1000.0 * flt_duration_min/60.0 ,1)

    #on transforme la durée de vol en format affichable
    flt_duration_str = maths_for_map.fct_time_str(flt_duration_min)

    # on prépare les futures colonnes du df
    apt_dep = ""
    apt_arr = ""
    apt_dep_icao = ""
    apt_arr_icao = ""

    # On lève une alerte si l'avion est trop haut au départ ou à l'arrivée, mais on continue. Par exemple, le vol est coupé par adsb-ex au moment du changement de jour UTC
    # altitude en mètre
    if elev_ini >= 4500:
        apt_dep = "A/C in cruise"
        apt_dep_icao = "A/C in cruise"
        print("départ A/C in cruise")

    if elev_last >= 3500:
        apt_arr = "A/C in cruise"
        apt_arr_icao = "A/C in cruise"
        print("arrivée A/C in cruise")

    return [regis, icao, dep_date_only_utc, dep_date_utc, arr_date_utc, flt_duration_min, flt_duration_str,
            apt_dep, apt_arr, apt_dep_icao, apt_arr_icao, lat_ini, long_ini, lat_last, long_last, flt_co2, csv_relatif]


#%% meilleure fonction du projet, pour une latitude et une longitude donnée, on donne l'aéroport le plus proche.
def fct_get_airport_from_lat_lon(lat_x, lon_x, apt_name_x):

    #on traite le cas des vols en cruise à part car sinon, si l'A/C en cruise à 30000ft au dessus d'un aéroport, le code dessous va considérer que c'est l'aéroport utilisé.
    if apt_name_x == "A/C in cruise":
        return "A/C in cruise", "A/C in cruise"

    else:
        # pas obligé je pense de faire copy
        df_airports_filtered = df_airports.copy()

        # on créé 2 colonnes avec l'écart lat & lon trajectoire et lat & lon aéroports
        df_airports_filtered["sub_lat"] = abs(df_airports_filtered["latitude_deg"] - lat_x)
        df_airports_filtered["sub_lon"] = abs(df_airports_filtered["longitude_deg"] - lon_x)

        # on suppose que les points sont assez proches pour calculer "simplement" la distance cartésienne entre les deux points, sans passer par une géodésique.
        # on cherche le point (sub_lat;sub_lon) qui a la plus petite distance à (0;0)
        df_airports_filtered["distance"] = np.sqrt(df_airports_filtered["sub_lat"]**2 + df_airports_filtered["sub_lon"]**2)

        # on identifie l'index de la plus courte distance facielemnt grâce à idxmin
        id_min = df_airports_filtered["distance"].idxmin()

        # on l'applique pour trouver le nom et l'icao de l'aéroport
        apt_x = df_airports_filtered["name"].iloc[id_min]
        apt_x_icao = df_airports_filtered["airport_icao"].iloc[id_min]

        #juste au cas où, si aéroport un peu loin, on lève une alerte mais on continue
        dist = df_airports_filtered["distance"].iloc[id_min]
        if dist > 0.1:
            print(f"!!! attention aéroport loin de l'avion: {dist} - {apt_x} !!!")

        return apt_x, apt_x_icao

#%%
def fct_get_all_data(df_new, list_csv, regis, icao, co2):
    #pour chaque nouveau vol, et donc chaque csv unique, on se sert du csv pour générer
    #toutes les infos (1ère et dernière positions, temps de vol, CO2 émis, etc)
    for csv in list_csv:
        item = fct_get_data_from_csv(csv, regis, icao, co2)
        df_item = pd.DataFrame([item], columns = list(df_new.columns))

        # on regroupe tous les nouveaux vols du même avions
        df_new = pd.concat([df_new, df_item], ignore_index=True)

    #definir types du nouveau df pour simplifier les futures tâches
    df_new["departure_date_utc"] = pd.to_datetime(df_new["departure_date_utc"], utc=True)
    df_new["arrival_date_utc"] = pd.to_datetime(df_new["arrival_date_utc"], utc=True)
    df_new["departure_date_only_utc_map"] = pd.to_datetime(df_new["departure_date_only_utc"], utc=True)#pour map/strftime
    df_new = df_new.astype({"co2_emission_tonnes":"float", "flight_duration_min":"float","latitude_dep":"float", "longitude_dep":"float","latitude_arr":"float", "longitude_arr":"float"})

    #find airport and add info with lambda and apply (et grâce aux 1ère et dernière positions du csv que l'on a trouvé avec "fct_get_data_from_csv"
    #fonction assez géniale en toute modestie
    df_new[["airport_departure","airport_dep_icao"]] = df_new.apply(lambda x: fct_get_airport_from_lat_lon(x["latitude_dep"], x["longitude_dep"], x["airport_departure"]), axis=1, result_type ="expand")
    df_new[["airport_arrival","airport_arr_icao"]] = df_new.apply(lambda x: fct_get_airport_from_lat_lon(x["latitude_arr"], x["longitude_arr"], x["airport_arrival"]), axis=1, result_type ="expand")


    return df_new


#%%