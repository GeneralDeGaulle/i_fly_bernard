# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 22:13:30 2022

script offline et séparé des autres, qui sert à regénérer facilement les plots d'un vol quand il y a eu un souci avec la version automatique

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
registration_ac = "F-HJJJ"
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


#%%
df_new_flights_only = df_ac_data.iloc[[1]]


#%%
#definir types
df_new_flights_only["departure_date_only_utc_map"] = pd.to_datetime(df_new_flights_only["departure_date_only_utc"])#pour map/strftime
df_new_flights_only = df_new_flights_only.astype({"co2_emission_tonnes":"float", "flight_duration_min":"float","latitude_dep":"float", "longitude_dep":"float","latitude_arr":"float", "longitude_arr":"float"})

#plot map
for new_flight in df_new_flights_only.itertuples():
    co2_new = new_flight.co2_emission_tonnes
    tps_vol_new = new_flight.flight_duration_str
    path_csv_flight = new_flight.path_csv
    date_map = new_flight.departure_date_only_utc_map.strftime("%#d %B %Y")

    csv_to_map.fct_csv_2_map(path_csv_flight, registration_ac, date_map, co2_new, tps_vol_new, ac_proprio)



#%%
# path_flight_csv = r"C:\Users\Michel\Desktop\Michel\Sciences\1-Ateliers\Atelier_sw\python\python_i_fly_bernard_2\output\F-HMBY\2022-07-17\leg_1\F-HMBY_baro_2022-07-17_leg_1.csv"

# registration_ac = "F-HMBY"
# icao24_ac = "39b038"
# co2_ac = 4700
# ac_proprio = "avion du groupe Bouygues"



