# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 17:24:50 2022

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import os

import locale
locale.setlocale(locale.LC_TIME,"");


#%%
from module import csv_to_map


#%%
# =============================================================================
registration_ac = "F-HMBY"
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
df_vols_tbc.loc[:,"next_flight_csv"] = df_vols_tbc["path_csv"].shift(1)

df_vols_tbc = df_ac_data[(df_vols_tbc["airport_arrival"] == "A/C in cruise") &
                         (df_vols_tbc["next_flight_departure"] == "A/C in cruise") &
                         (df_vols_tbc["arrival_date_utc"].dt.strftime("%H") == "23")]

#%% fusionner csv


#%% refaire tourner le code pour obtenir les infos du vols


#%% ajouter new flight et cleaner les anciens


#%% si ok, en registrer

