# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 17:24:50 2022

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import os
import numpy as np


#%%
from src.core import get_new_df_data


#%% concat all flights
def fct_concat_all_flights(df_avion, path):
    df_all_flights = pd.DataFrame()
    list_ac = df_avion["registration"].values

    # pour concatener tous les vols dans un seul csv
    for ac in list_ac:
        path_ac = os.path.join(path, "output", ac, f"{ac}_flight_data_all.csv")
        df = pd.read_csv(path_ac, delimiter = ",")
        df_all_flights = pd.concat([df_all_flights, df])

    # "if" to avoid a corner case condition if everything is empty
    if not df_all_flights.empty:
        df_all_flights["departure_date_utc"] = pd.to_datetime(df_all_flights["departure_date_utc"], utc=True)
        df_all_flights["arrival_date_utc"] = pd.to_datetime(df_all_flights["arrival_date_utc"], utc=True)
        df_all_flights = df_all_flights.sort_values(by=["departure_date_utc"], ascending = False)
        df_all_flights = df_all_flights.reset_index(drop=True)

        df_all_flights["routes"] = df_all_flights["airport_departure"] + " - " + df_all_flights["airport_arrival"]
        df_all_flights["routes"] = df_all_flights["routes"].astype('category')

        list_colonnes = df_all_flights.columns.tolist()

        # pour ajouter un nom intelligible du propriétaire
        for aircraft in list_ac:
            nom = df_avion[df_avion["registration"] == aircraft].proprio.values[0]
            df_all_flights.loc[df_all_flights["registration"] == aircraft,"propriétaire"] = nom

            #pour mettre le propriétaire en premier
            df_all_flights = df_all_flights.loc[:,["propriétaire" ] + list_colonnes]

            #pour sauvegarder
            path_all_ac = os.path.join(path, "output", "all_flights_data.csv")
            df_all_flights.to_csv(path_all_ac, index=False, encoding="utf-8-sig")

            print("---------------------------")
            print("--- all_flights_data.csv généré ---")

    # to avoid a corner case condition if everything is empty (and investigate)
    else:
        print()
        print(f"!!! no flight to merge - check all 'aircraft_flight_data.csv' files !!!")
        print()


#%%

