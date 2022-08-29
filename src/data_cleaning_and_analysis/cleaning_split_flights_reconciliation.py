# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 17:24:50 2022

Standalone script to find and correct flights which have been split by adsb-exchange.com
at midnight UTC.

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import os
import numpy as np

import locale
locale.setlocale(locale.LC_TIME,"");


#%%
from src.core import get_new_df_data
from src.core import csv_to_map


#%%


# script à utiliser avec précaution et avec vérification manuelle que c'est bien un vol
# coupé en 2 !


#%%
# =============================================================================
registration_ac = "F-HMBY"
# =============================================================================

#%% define path
path = os.getcwd()
path_avions = os.path.join(path, "input","avions.csv")

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

df_vols_tbc_1 = df_vols_tbc[(df_vols_tbc["airport_arrival"] == "A/C in cruise") &
                          (df_vols_tbc["next_flight_departure"] == "A/C in cruise")]

df_vols_to_be_merged_1 = df_vols_tbc_1[(df_vols_tbc_1["arrival_date_utc"].dt.strftime("%H") >= "23") &
                         (df_vols_tbc_1["diff_with_next"].dt.seconds/3600 <= 4) &
                         (df_vols_tbc_1["diff_with_next"].dt.days == 0)]

df_vols_to_be_merged = pd.concat([df_vols_to_be_merged_1])


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

    os.remove(path_csv_ini)

    list_new_csv.append(path_merged)
    list_next_csv.append(path_csv_next)


#%% refaire tourner le code pour obtenir les infos du vols
df_new_flights_empty = pd.DataFrame(columns = df_ac_data.columns)

#récupération des infos pour tous les nouveaux vols de cet avion
df_new_flights_only = get_new_df_data.fct_get_all_data(df_new_flights_empty,
                                                       list_new_csv,
                                                       registration_ac,
                                                       icao24_ac, co2_ac, ac_proprio, quiet = 0)


#plot map grâce à plotly avec les infos requises pour le titre de l'image
for new_flight in df_new_flights_only.itertuples():
    co2_new = new_flight.co2_emission_tonnes
    tps_vol_new = new_flight.flight_duration_str
    path_csv_flight = new_flight.path_csv
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
df_complete = pd.concat([df_ac_data, df_new_flights_only])
df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending = False)


#%% si ok, enregistrer et supprimer ancien folder
df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")

for next_flight_csv in list_next_csv:
    os.remove(next_flight_csv)
    os.rmdir(os.path.dirname(next_flight_csv))


