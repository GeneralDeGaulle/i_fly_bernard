# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 22:13:30 2022

script offline et séparé des autres, qui sert à regénérer toutes les données des fichiers
"ac_flight_data_all.csv" à partir du path_csv contenu dans ce même fichier.

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import os


#%%
from module import csv_to_map
from module import get_new_df_data


#%% define path
path = os.getcwd()
path_avions = os.path.join(path, r"input\avions.csv")


#%%
df_avion = pd.read_csv(path_avions, delimiter = ",")


#%% pour tous les avions
for aircraft_row in df_avion.itertuples():
    #define variables pour un avion
    registration_ac = aircraft_row.registration
    icao24_ac = str(aircraft_row.icao24)
    co2_ac = aircraft_row.co2_kg_per_hour
    print(registration_ac)
    # break

    path_flight_data = os.path.join(path, "output", registration_ac)
    path_flight_data_csv = os.path.join(path_flight_data, f"{registration_ac}_flight_data_all.csv")

    df_ac_data = pd.read_csv(path_flight_data_csv, delimiter = ",")
    df_ac_data["departure_date_utc"] = pd.to_datetime(df_ac_data["departure_date_utc"], utc=True)
    df_ac_data["arrival_date_utc"] = pd.to_datetime(df_ac_data["arrival_date_utc"], utc=True)


    df_new_flights_empty = pd.DataFrame(columns = df_ac_data.columns)

    # pour recalculer les données du vol à partir du csv
    list_new_csv = list(df_ac_data.path_csv.values)

    #récupération des infos pour tous les nouveaux vols de cet avion
    df_ac_data_new = get_new_df_data.fct_get_all_data(df_new_flights_empty,
                                                           list_new_csv,
                                                           registration_ac,
                                                           icao24_ac, co2_ac)

    # #clean and save data
    #on nettoie new flight avant de le fusionner
    df_ac_data_new = df_ac_data_new.drop(columns=["departure_date_only_utc_map"])

    #une fois fini on regroupe tous les vols.
    df_complete = df_ac_data_new
    df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending = False)

    #puis on sauvegarde
    df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")


#%% pour un seul avion
registration_ac = "F-GBOL"

df_avion = df_avion[df_avion["registration"] == registration_ac]
icao24_ac = df_avion.icao24.values[0]
co2_ac = df_avion.co2_kg_per_hour.values[0]
ac_proprio = df_avion.proprio.values[0]


path_flight_data = os.path.join(path, "output", registration_ac)
path_flight_data_csv = os.path.join(path_flight_data, f"{registration_ac}_flight_data_all.csv")

df_ac_data = pd.read_csv(path_flight_data_csv, delimiter = ",")
df_ac_data["departure_date_utc"] = pd.to_datetime(df_ac_data["departure_date_utc"], utc=True)
df_ac_data["arrival_date_utc"] = pd.to_datetime(df_ac_data["arrival_date_utc"], utc=True)

df_new_flights_empty = pd.DataFrame(columns = df_ac_data.columns)

# pour recalculer les données du vol à partir du csv
list_new_csv = list(df_ac_data.path_csv.values)

#récupération des infos pour tous les nouveaux vols de cet avion
df_ac_data_new = get_new_df_data.fct_get_all_data(df_new_flights_empty,
                                                       list_new_csv,
                                                       registration_ac,
                                                       icao24_ac, co2_ac)

# #clean and save data
#on nettoie new flight avant de le fusionner
df_ac_data_new = df_ac_data_new.drop(columns=["departure_date_only_utc_map"])

#une fois fini on regroupe tous les vols.
df_complete = df_ac_data_new
df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending = False)

#puis on sauvegarde
df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")



