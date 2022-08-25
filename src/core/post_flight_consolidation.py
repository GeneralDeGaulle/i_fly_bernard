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
        print(f"--- {registration_ac} - {m} vols dont l'aéroport a été modifiés ---")


#%% vol de - de 5min ou -10min avec meme airport dep = arr
def fct_short_flight(df_data):
    registration_ac = df_data.registration.iloc[0]

    taille_avant = len(df_data)

    df_data = df_data[df_data["flight_duration_min"] >= 5]
    df_data = df_data[(df_data["airport_arrival"] != df_data["airport_departure"]) |
                      (df_data["flight_duration_min"] >= 10)]

    taille_apres = len(df_data)

    m = taille_avant - taille_apres

    if m != 0:
        print(f"!!! {registration_ac} - {m} vols dont l'aéroport a été modifiés !!!")

    return df_data


#%% verification si deux vols ont été fusionnés par erreur par adsb
def fct_check_2flights_in1(df_data, output = 0):
    taille_avant = len(df_data)

    # on enlève les vols de moins de 2h car ils sont nécessairement plus lent (moins de phase
    # de croisiere à haute vitesse et moins intéressant relativement aux données de vols perdues
    df_data = df_data[df_data["flight_duration_min"] >= 120]

    # calcul de la durée théorique du vol en utilisant une vitesse moyenne pour ce genre de jets.
    # on a calculé sur les 2ans de data 606 km/h pour les milliardaires ; 559 pour valljet.
    # On prends 500 pour avoir une marge
    df_data["flight_duration_theorique_h"] = df_data["distance_km"] / 500.0

    # on estime que le vol a été étrangement long s'il a pris une heure en plus que la moyenne
    df_data["flight_took_too_long"] = (df_data["flight_duration_min"] / 60.0
                                       - df_data["flight_duration_theorique_h"]) > 0.5

    # on ne garde que les vols "problématiques"
    df_data = df_data[(df_data["flight_took_too_long"] == True)]

    # on clean les colonnes
    df_data = df_data.drop(columns=["flight_duration_theorique_h", "flight_took_too_long"])

    # on vérifie s'il y a bien un gap dans le csv (et si ce n'est pas un vol lent, ou tour de piste ou autre)
    df_data = fct_check_gap_in_flight(df_data)

    taille_apres = len(df_data)
    m = taille_avant - taille_apres

    if m != 0:
        if output == 0:
            print(f"!!! {m} vols avec un temps de vol trop long et un gap de position !!!")
        else:
            print(f"!!! {m} vols avec un temps de vol trop long et un gap de position !!!")
            return df_data


#%% verification un vol étrangement long à un gap
def fct_check_gap_in_flight(df_data):
    # on regarde vol par vol si le csv n'a pas un trou
    for i in df_data.index:
        path_csv = df_data.loc[i].path_csv

        # on charge le csv du vol concerné
        df = pd.read_csv(path_csv)
        df["time"] = pd.to_datetime(df["time"], utc=True)

        # on regarde si dans le csv, deux points consécutifs on un écart de plus d'1h afin de
        # rechercher les trous de trajectoires. Inférieur à 1h n'est pas intéressant en termes de pertes de données
        df["diff_time"] = df["time"].shift(-1) - df["time"]
        df["diff_time"] = df["diff_time"].apply(lambda x: x.seconds/3600.0)

        df_gaps = df[df["diff_time"] >= 1]

        if df_gaps.empty:
            df_data = df_data.drop([i])

    return df_data


#%%