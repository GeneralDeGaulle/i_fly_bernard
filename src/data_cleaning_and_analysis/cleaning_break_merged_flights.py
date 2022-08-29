# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 17:24:50 2022

Standalone script to find and correct flights which have been mistakenly merged by adsb-exchange.com
due to signal loss

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import os


#%%
from src.core import post_flight_consolidation
from src.core import get_new_df_data


#%%


# script à utiliser avec précaution et avec vérification manuelle


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
gallons_ac = aircraft_row.us_gallons_per_hour


#%%
df_ac_data = pd.read_csv(path_flight_data_csv, delimiter = ",")
df_ac_data["departure_date_utc"] = pd.to_datetime(df_ac_data["departure_date_utc"], utc=True)
df_ac_data["arrival_date_utc"] = pd.to_datetime(df_ac_data["arrival_date_utc"], utc=True)


#%% identifier les vols à découper
df_tbc = post_flight_consolidation.fct_check_2flights_in1(df_ac_data, output = 1)


#%% visualiser les vols
post_flight_consolidation.fct_open_flights(df_tbc)


#%% sélectionner les vols à traiter
list_vols_index = [0]
df_to_break = df_tbc.iloc[list_vols_index]


#%% analyser les vols à breaker
path_csv_ini = os.path.join(path, df_to_break.path_csv.iloc[0])
path_folder_ini = os.path.dirname(path_csv_ini)
file_name_ini = os.path.splitext(os.path.basename(df_to_break.path_csv.iloc[0]))[0]

df_csv_ini = pd.read_csv(path_csv_ini)
df_csv_ini["time"] = pd.to_datetime(df_csv_ini["time"], utc=True)

# on regarde si dans le csv, deux points consécutifs on un écart de plus d'1h afin de
# rechercher les trous de trajectoires. Inférieur à 1h n'est pas intéressant en termes de pertes de données
df_csv_ini["diff_time_h"] = df_csv_ini["time"].shift(-1) - df_csv_ini["time"]
df_csv_ini["diff_time_h"] = df_csv_ini["diff_time_h"].apply(lambda x: x.seconds/3600.0)
df_gaps = df_csv_ini[df_csv_ini["diff_time_h"] >= 1]

df_gaps = df_gaps.sort_values(by="diff_time_h", ascending = False)


#%% on construit les nouveaux csv et on les plots pour vérifier
df_break_point = df_gaps.iloc[0]

path_csv_flight_1 = os.path.join(path_folder_ini, f"{file_name_ini}_break_1.csv")
path_csv_flight_2 = os.path.join(path_folder_ini, f"{file_name_ini}_break_2.csv")

df_csv_flight_1 = df_csv_ini.iloc[0:df_break_point.name]
df_csv_flight_2 = df_csv_ini.iloc[df_break_point.name + 1:]

post_flight_consolidation.plot_df_csv(df_csv_flight_1, path_csv_flight_1)
post_flight_consolidation.plot_df_csv(df_csv_flight_2, path_csv_flight_2)

df_csv_flight_1.to_csv(path_csv_flight_1, index=False, encoding="utf-8-sig")
df_csv_flight_2.to_csv(path_csv_flight_2, index=False, encoding="utf-8-sig")


#%% on regénère les données pour les nouveaux vols
list_new_csv = [path_csv_flight_1, path_csv_flight_2]

#récupération des infos pour tous les nouveaux vols de cet avion
df_new_flights_empty = pd.DataFrame(columns = df_ac_data.columns)
df_new_flights_only = get_new_df_data.fct_get_all_data(df_new_flights_empty, list_new_csv,
                                                       registration_ac, icao24_ac, co2_ac,
                                                       ac_proprio, gallons_ac,
                                                       quiet = 0)
#on nettoie
df_new_flights_only = df_new_flights_only.drop(columns=["departure_date_only_utc_map"])


#%% on clean le df_initial, et on merge le nouveau avec l'ancien et on sauvegarde
df_ac_data = df_ac_data.drop(list(df_to_break.index))

df_complete = pd.concat([df_ac_data, df_new_flights_only])
df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending = False)


df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")


#%%

