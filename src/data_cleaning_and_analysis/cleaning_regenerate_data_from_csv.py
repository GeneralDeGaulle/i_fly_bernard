# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 22:13:30 2022

script qui sert à regénérer toutes les données des fichiers "ac_flight_data_all.csv" à partir
du path_csv contenu dans ce même fichier.

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import os


#%%
from src.core import get_new_df_data
from src.core import post_flight_consolidation


#%% define path
path = os.getcwd()
path_avions = os.path.join(path, r"input\avions.csv")

df_avion = pd.read_csv(path_avions, delimiter=",")


#%% pour repositionner les colonnes si besoin
# list_col = ["propriétaire", "registration", "icao24", "departure_date_only_utc", "departure_date_utc",
#             "arrival_date_utc", "airport_departure", "airport_arrival", "flight_duration_str",
#             "flight_duration_min", "kerosene_litres", "co2_emission_tonnes", "distance_km", "iso_country_dep", "iso_country_arr", "routes",
#             "airport_dep_icao", "airport_arr_icao", "latitude_dep", "longitude_dep",
#             "latitude_arr", "longitude_arr", "altitude_dep_m", "altitude_arr_m","path_csv"]

#%% pour tous les avions
for aircraft_row in df_avion.itertuples():
    # define variables pour un avion
    registration_ac = aircraft_row.registration
    icao24_ac = str(aircraft_row.icao24)
    co2_ac = aircraft_row.co2_kg_per_hour
    ac_proprio = aircraft_row.proprio
    gallons_ac = aircraft_row.us_gallons_per_hour
    print(registration_ac)
    # break

    path_flight_data = os.path.join(path, "output", registration_ac)
    path_flight_data_csv = os.path.join(path_flight_data, f"{registration_ac}_flight_data_all.csv")

    df_ac_data = pd.read_csv(path_flight_data_csv, delimiter=",")

    # pour recalculer les données du vol à partir du csv
    list_new_csv = list(df_ac_data.path_csv.values)

    # pour repositionner les colonnes si besoin
    # df_new_flights_empty = pd.DataFrame(columns = list_col)

    # df vide
    df_new_flights_empty = pd.DataFrame(columns=df_ac_data.columns)

    # récupération des infos pour tous les nouveaux vols de cet avion
    df_ac_data_new = get_new_df_data.fct_get_all_data(
        df_new_flights_empty,
        list_new_csv,
        registration_ac,
        icao24_ac,
        co2_ac,
        ac_proprio,
        gallons_ac,
        quiet=1)

    # #clean and save data
    # on nettoie new flight avant de le fusionner
    df_ac_data_new = df_ac_data_new.drop(columns=["departure_date_only_utc_map"])

    # on garde le même nom par simplicité.
    df_complete = df_ac_data_new.copy()
    df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending=False)

    # on teste le nouveau df avec les fonctions de consolidations.En fonction de la vérification,
    # soit on applique les modifs, soit une alerte.
    df_complete = post_flight_consolidation.fct_airport_vs_cruise(df_complete)
    df_complete = post_flight_consolidation.fct_short_flight(df_complete)
    post_flight_consolidation.fct_check_2flights_in1(df_complete)
    post_flight_consolidation.fct_check_reconciliation(df_complete)

    # puis on sauvegarde
    df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")
    print()


#%% pour un seul avion
registration_ac = "F-GBOL"

df_avion = df_avion[df_avion["registration"] == registration_ac]
icao24_ac = str(df_avion.icao24.values[0])
co2_ac = df_avion.co2_kg_per_hour.values[0]
ac_proprio = df_avion.proprio.values[0]
gallons_ac = df_avion.us_gallons_per_hour.values[0]

path_flight_data = os.path.join(path, "output", registration_ac)
path_flight_data_csv = os.path.join(path_flight_data, f"{registration_ac}_flight_data_all.csv")
df_ac_data = pd.read_csv(path_flight_data_csv, delimiter=",")

# pour recalculer les données du vol à partir du csv
list_new_csv = list(df_ac_data.path_csv.values)

# pour repositionner les colonnes si besoin
# df_new_flights_empty = pd.DataFrame(columns = list_col)

# df vide
df_new_flights_empty = pd.DataFrame(columns=df_ac_data.columns)
# récupération des infos pour tous les nouveaux vols de cet avion
df_ac_data_new = get_new_df_data.fct_get_all_data(
    df_new_flights_empty,
    list_new_csv,
    registration_ac,
    icao24_ac,
    co2_ac,
    ac_proprio,
    gallons_ac,
    quiet=1)

# #clean and save data
# on nettoie new flight avant de le fusionner
df_ac_data_new = df_ac_data_new.drop(columns=["departure_date_only_utc_map"])

# on garde le même nom par simplicité.
df_complete = df_ac_data_new.copy()
df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending=False)

# on teste le nouveau df avec les fonctions de consolidations.En fonction de la vérification,
# soit on applique les modifs, soit une alerte.
df_complete = post_flight_consolidation.fct_airport_vs_cruise(df_complete)
df_complete = post_flight_consolidation.fct_short_flight(df_complete)
post_flight_consolidation.fct_check_2flights_in1(df_complete)
post_flight_consolidation.fct_check_reconciliation(df_complete)


# puis on sauvegarde
df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")


#%% concat all aircraft df in one csv
post_flight_consolidation.fct_concat_all_flights(df_avion, path, quiet=0)
