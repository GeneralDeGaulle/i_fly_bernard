# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 17:24:50 2022

script contenant quelques fonctions utiles pour le post flight

@author: GeneralDeGaulle
"""

#%%
import pandas as pd
import os
import numpy as np

from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service


#%%
path = os.getcwd()
path_avions = os.path.join(path, "input","avions.csv")

df_avion = pd.read_csv(path_avions, delimiter = ",")


#%% concat all flights
def fct_concat_all_flights(df_avion, path):
    df_all_flights = pd.DataFrame()
    list_ac = df_avion["registration"].values

    # pour concatener tous les vols dans un seul csv
    for ac in list_ac:
        path_ac = os.path.join(path, "output", ac, f"{ac}_flight_data_all.csv")
        df = pd.read_csv(path_ac, delimiter = ",")
        df_all_flights = pd.concat([df_all_flights, df])


    df_all_flights["departure_date_utc"] = pd.to_datetime(df_all_flights["departure_date_utc"], utc=True)
    df_all_flights["arrival_date_utc"] = pd.to_datetime(df_all_flights["arrival_date_utc"], utc=True)
    df_all_flights = df_all_flights.sort_values(by=["departure_date_utc"], ascending = False)
    df_all_flights = df_all_flights.reset_index(drop=True)


    #pour sauvegarder
    path_all_ac = os.path.join(path, "output", "all_flights_data.csv")
    df_all_flights.to_csv(path_all_ac, index=False, encoding="utf-8-sig")

    print("---------------------------")
    print("--- all_flights_data.csv généré ---")


#%% ouvre adsb-ex sur les vols à problèmes
def fct_open_flights(df_issue):

    browser = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

    for flights in df_issue.itertuples():
        date = flights.departure_date_only_utc
        icao = flights.icao24

        url = "https://globe.adsbexchange.com/?icao=" + icao + "&showTrace=" + date

        browser.switch_to.new_window("tab")
        browser.get(url)


#%% apt cruise = précédent ou suivant
def fct_airport_vs_cruise(df_data):

    registration_ac = df_data.registration.iloc[0]

    df_data.loc[:,"next_flight_departure"] = df_data["airport_departure"].shift(1)
    df_data.loc[:,"previous_flight_arrival"] = df_data["airport_arrival"].shift(-1)

    condition_cruise_arr = ((df_data["airport_arrival"] == "A/C in cruise") &
                 (df_data["next_flight_departure"] != "A/C in cruise"))

    condition_cruise_dep = ((df_data["airport_departure"] == "A/C in cruise") &
                 (df_data["previous_flight_arrival"] != "A/C in cruise"))

    m = len(df_data[condition_cruise_arr]) + len(df_data[condition_cruise_dep])

    if m > 0:
        df_data.loc[condition_cruise_arr, "airport_arrival"] = df_data.loc[condition_cruise_arr,"next_flight_departure"]
        df_data.loc[condition_cruise_dep, "airport_departure"] = df_data.loc[condition_cruise_dep, "previous_flight_arrival"]

        #cleaning
        df_data = df_data.drop(columns=["next_flight_departure","previous_flight_arrival"])
        print(f"--- {registration_ac} - {m} vols dont l'aéroport a été modifiés ---")

        return df_data

    else:
        print(f"{registration_ac} - {m} vols dont l'aéroport a été modifiés")


#%%
