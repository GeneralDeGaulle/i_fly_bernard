# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 17:24:50 2022

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import os
import numpy as np

import locale
locale.setlocale(locale.LC_TIME,"");


#%%
from module import get_new_df_data
from module import csv_to_map


#%%
# =============================================================================
registration_ac = "F-HFHP"
# =============================================================================

#%% define path
path = os.getcwd()
path_avions = os.path.join(path, r"input\avions.csv")

path_flight_data = os.path.join(path, "output", registration_ac)
path_flight_data_csv = os.path.join(path_flight_data, f"{registration_ac}_flight_data_all.csv")


#%% load generic data
df_avion = pd.read_csv(path_avions, delimiter = ",")

df_avion = df_avion[df_avion["registration"] == registration_ac]

icao24_ac = df_avion.icao24.values[0]
co2_ac = df_avion.co2_kg_per_hour.values[0]
ac_proprio = df_avion.proprio.values[0]


#%%
df_ac_data = pd.read_csv(path_flight_data_csv, delimiter = ",")
df_ac_data["departure_date_utc"] = pd.to_datetime(df_ac_data["departure_date_utc"], utc=True)
df_ac_data["arrival_date_utc"] = pd.to_datetime(df_ac_data["arrival_date_utc"], utc=True)


#%% identifier doublette de vol à réconcilier
df_vols_tbc = df_ac_data.copy()

df_vols_tbc.loc[:,"next_flight_departure"] = df_vols_tbc["airport_departure"].shift(1)
df_vols_tbc.loc[:,"next_flight_departure_date"] = df_vols_tbc["departure_date_utc"].shift(1)
df_vols_tbc.loc[:,"diff_with_next"] = df_vols_tbc["next_flight_departure_date"] - df_vols_tbc["arrival_date_utc"]
df_vols_tbc.loc[:,"next_flight_csv"] = df_vols_tbc["path_csv"].shift(1)

df_vols_tbc = df_vols_tbc[(df_vols_tbc["airport_arrival"] == "A/C in cruise") &
                         (df_vols_tbc["next_flight_departure"] == "A/C in cruise") &
                         (df_vols_tbc["airport_departure"] != "A/C in cruise")]


df_vols_to_be_merged = df_vols_tbc[(df_vols_tbc["arrival_date_utc"].dt.strftime("%H") >= "23") &
                         (df_vols_tbc["diff_with_next"].dt.seconds/3600 <= 4)]

#souvent des vols où on ne capte pas à l'arrivée et donc pas de second leg à fusionner
df_vols_tbc_not = df_vols_tbc[(df_vols_tbc["arrival_date_utc"].dt.strftime("%H") < "23") |
                              (df_vols_tbc["diff_with_next"].dt.seconds/3600 > 4)]


#%% fusionner csv
list_new_csv = []
list_next_csv = []
for flight in df_vols_to_be_merged.itertuples():
    path_csv_ini = os.path.join(path, flight.path_csv)
    path_csv_next = os.path.join(path, flight.next_flight_csv)

    df_csv_ini = pd.read_csv(path_csv_ini)
    df_csv_next = pd.read_csv(path_csv_next)

    df_csv_merged = pd.concat([df_csv_ini, df_csv_next], ignore_index=True)

    file_name_ini = os.path.basename(path_csv_ini)
    file_name_merged = os.path.splitext(file_name_ini)[0] + "_merged.csv"

    path_folder_ini = os.path.dirname(path_csv_ini)
    path_merged = os.path.join(path_folder_ini, file_name_merged)
    df_csv_merged.to_csv(path_merged, index=False, encoding="utf-8-sig")

    list_new_csv.append(path_merged)
    list_next_csv.append(path_csv_next)


#%% refaire tourner le code pour obtenir les infos du vols
df_new_flights_only = pd.DataFrame(columns = df_ac_data.columns)

#pour chaque nouveau vol, et donc chaque csv unique, on se sert du csv pour générer toutes les infos (1ère et dernière positions, temps de vol, CO2 émis, etc)
for csv_file in list_new_csv:
    item = get_new_df_data.fct_get_data_from_csv(csv_file, registration_ac, icao24_ac, co2_ac)
    df_item = pd.DataFrame([item], columns = list(df_ac_data.columns))

    # on regroupe tous les nouveaux vols du même avions
    df_new_flights_only = pd.concat([df_new_flights_only, df_item], ignore_index=True)

#definir types du nouveau df pour simplifier les futures tâches
df_new_flights_only["departure_date_utc"] = pd.to_datetime(df_new_flights_only["departure_date_utc"])
df_new_flights_only["arrival_date_utc"] = pd.to_datetime(df_new_flights_only["arrival_date_utc"])
df_new_flights_only["departure_date_only_utc_map"] = pd.to_datetime(df_new_flights_only["departure_date_only_utc"])#pour map/strftime
df_new_flights_only = df_new_flights_only.astype({"co2_emission_tonnes":"float", "flight_duration_min":"float","latitude_dep":"float", "longitude_dep":"float","latitude_arr":"float", "longitude_arr":"float"})

#find airport and add info with lambda and apply (et grâce aux 1ère et dernière positions du csv que l'on a trouvé avec "fct_get_data_from_csv"
#fonction assez géniale en toute modestie
df_new_flights_only[["airport_departure","airport_dep_icao"]] = df_new_flights_only.apply(lambda x: get_new_df_data.fct_get_airport_from_lat_lon(x["latitude_dep"], x["longitude_dep"], x["airport_departure"]), axis=1, result_type ="expand")
df_new_flights_only[["airport_arrival","airport_arr_icao"]] = df_new_flights_only.apply(lambda x: get_new_df_data.fct_get_airport_from_lat_lon(x["latitude_arr"], x["longitude_arr"], x["airport_arrival"]), axis=1, result_type ="expand")


#plot map grâce à plotly avec les infos requises pour le titre de l'image
for new_flight in df_new_flights_only.itertuples():
    co2_new = new_flight.co2_emission_tonnes
    tps_vol_new = new_flight.flight_duration_str
    path_csv_flight = new_flight.path_csv
    print(path_csv_flight)
    date_map = new_flight.departure_date_only_utc_map.strftime("%#d %B %Y")

    csv_to_map.fct_csv_2_map(path_csv_flight, registration_ac, date_map, co2_new, tps_vol_new, ac_proprio)


#clean and save data
#on nettoie new flight avant de le fusionner
df_new_flights_only = df_new_flights_only.drop(columns=["departure_date_only_utc_map"])



#%% cleaner les anciens
list_vol_ini = np.array(df_vols_to_be_merged.index)
list_vol_next = list_vol_ini - 1 #car vol rangé du plus récent au plus ancien

df_ac_data = df_ac_data.drop(list_vol_ini)
df_ac_data = df_ac_data.drop(list_vol_next)



#%%

#une fois fini on regroupe tous les vols.
#Pas de check de duplicate car protection dans "fct_kml_2_folder"
# et dans la gestion de la date de dernier check dans df_avion. Peut être amélioré
df_complete = pd.concat([df_ac_data, df_new_flights_only])
df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending = False)


#%% si ok, enregistrer et supprimer ancien folder
df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")

for next_flight_csv in list_next_csv:
    os.remove(next_flight_csv)
    os.rmdir(os.path.dirname(next_flight_csv))


