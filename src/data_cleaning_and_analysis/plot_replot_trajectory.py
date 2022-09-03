# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 22:13:30 2022

script offline et séparé des autres, qui sert à regénérer facilement les plots d'un vol quand
il y a eu un souci avec la version automatique

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import os

import locale

locale.setlocale(locale.LC_TIME, "")


#%%
from src.core import csv_to_map
from src.core import get_new_df_data


#%%

# =============================================================================
registration_ac = "F-HFHP"
# =============================================================================

#%% define path
path = os.getcwd()
path_avions = os.path.join(path, "input", "avions.csv")

path_flight_data = os.path.join(path, "output", registration_ac)
path_flight_data_csv = os.path.join(path_flight_data, f"{registration_ac}_flight_data_all.csv")


#%% load generic data
df_avion = pd.read_csv(path_avions, delimiter=",")

df_avion = df_avion[df_avion["registration"] == registration_ac]

icao24_ac = str(df_avion.icao24.values[0])
co2_ac = df_avion.co2_kg_per_hour.values[0]
ac_proprio = df_avion.proprio.values[0]


#%%
df_ac_data = pd.read_csv(path_flight_data_csv, delimiter=",")
df_ac_data["departure_date_utc"] = pd.to_datetime(df_ac_data["departure_date_utc"], utc=True)
df_ac_data["arrival_date_utc"] = pd.to_datetime(df_ac_data["arrival_date_utc"], utc=True)


#%%
list_new_vols_index = [1]
df_new_flights_only = df_ac_data.iloc[list_new_vols_index]

# df_new_flights_only.to_markdown(tablefmt="fancy_grid")


#%% pour recalculer les données du vol à partir du csv
df_new_flights_empty = pd.DataFrame(columns=df_ac_data.columns)

list_new_csv = list(df_new_flights_only.path_csv.values)

# récupération des infos pour tous les nouveaux vols de cet avion
df_new_flights_only = get_new_df_data.fct_get_all_data(
    df_new_flights_empty,
    list_new_csv,
    registration_ac,
    icao24_ac,
    co2_ac,
    ac_proprio,
    gallons_ac,
    quiet=0)


#%%
# definir types
df_new_flights_only["departure_date_only_utc_map"] = pd.to_datetime(df_new_flights_only["departure_date_only_utc"])
df_new_flights_only = df_new_flights_only.astype(
    {
        "co2_emission_tonnes": "float",
        "flight_duration_min": "float",
        "latitude_dep": "float",
        "longitude_dep": "float",
        "latitude_arr": "float",
        "longitude_arr": "float"
    })

# plot map
for new_flight in df_new_flights_only.itertuples():
    co2_new = new_flight.co2_emission_tonnes
    tps_vol_new = new_flight.flight_duration_str
    path_csv_flight = new_flight.path_csv
    date_map = new_flight.departure_date_only_utc_map.strftime("%#d %B %Y")

    csv_to_map.fct_csv_2_map(
        path_csv_flight, registration_ac, date_map, co2_new, tps_vol_new, ac_proprio)


#%%
# clean and save data

# on supprime les anciens vols avant d'ajouter le nouveau
df_ac_data = df_ac_data.drop(list_new_vols_index)

# on nettoie new flight avant de le fusionner
df_new_flights_only = df_new_flights_only.drop(columns=["departure_date_only_utc_map"])

# une fois fini on regroupe tous les vols.
df_complete = pd.concat([df_ac_data, df_new_flights_only])
df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending=False)

# puis on sauvegarde
df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d %H:%M:%S"))


#%%
