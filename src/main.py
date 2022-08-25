# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 21:43:19 2022

Script principal qui, pour chaque avion dans "/input/avions.csv", utilise les autres scipts pour
rechercher de nouveaux vols, générer les cartes et calculer le CO2 associé.

@author: GeneralDeGaulle
"""

#%% import library
import pandas as pd
import os
import time

#pour le format de la date du titre de la carte
import locale
locale.setlocale(locale.LC_TIME,"");

#%%
start_time = time.time()

#%% import scripts
from src.core import adsb_exchange
from src.core import kml_to_csv
from src.core import get_new_df_data
from src.core import csv_to_map
from src.core import post_flight_consolidation


#%% define path
path_main = os.path.dirname(os.path.abspath(__file__))
path = os.path.abspath(os.path.join(path_main, os.pardir))

# pour être sûr que le path est le bon au cas où cwd() n'est pas correctement configuré.
os.chdir(path)


#%% load generic data
path_avions = os.path.join(path, "input","avions.csv")

df_avion = pd.read_csv(path_avions, delimiter = ",")
df_avion["last_check"] = pd.to_datetime(df_avion["last_check"], utc=True)

today_date = pd.to_datetime("now", utc=True)


#%% start of loop
n = 0

#on attaque la boucle for pour passer les avions l'un après l'autre
for aircraft_row in df_avion.itertuples():
    #define variables pour un avion
    registration_ac = aircraft_row.registration
    icao24_ac = str(aircraft_row.icao24)
    co2_ac = aircraft_row.co2_kg_per_hour
    last_check_date = aircraft_row.last_check
    ac_proprio = aircraft_row.proprio


    #load previous data
    path_flight_data = os.path.join(path, "output", registration_ac)
    path_flight_data_csv = os.path.join(path_flight_data, f"{registration_ac}_flight_data_all.csv")

    # pour créer le dossier si l'avion n'existe pas encore. pas le plus élégant mais efficace
    if not os.path.exists(path_flight_data):
        os.makedirs(path_flight_data, exist_ok=True)
        df_template = pd.read_csv(os.path.join(path, "input","template_flight_data_all.csv"))
        df_template.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")

    df_ac_data = pd.read_csv(path_flight_data_csv, delimiter = ",")
    df_ac_data["departure_date_utc"] = pd.to_datetime(df_ac_data["departure_date_utc"], utc=True)
    df_ac_data["arrival_date_utc"] = pd.to_datetime(df_ac_data["arrival_date_utc"], utc=True)


    #go sur adsb-exchange pour trouver les nouveau vols par rapport à la date du dernier check jusqu'à aujourd'hui
    list_new_flights_ac = []
    list_new_flights_ac = adsb_exchange.fct_adsbex_check_new_flights_and_kml(icao24_ac, registration_ac, path_flight_data, last_check_date)


    #si nouveau(x) vol(s), on continue, sinon stop et on passe à l'avion suivant.
    if list_new_flights_ac:
        print()
        print(f"--- {str(len(list_new_flights_ac))} new flights found for A/C {registration_ac} ---")
        print()

        #on déplace chaque kml dans le bon dossier.
        #mis en place car selenium/firefox ne permet pas de modifier dynamiquement le lieu de téléchargement
        list_folder_and_kml_paths = kml_to_csv.fct_kml_2_folder(list_new_flights_ac, path_flight_data)

        #si nouveau(x) vol(s), on continue (en effet, si on lance le programme plusieurs fois par jour, on peut avoir un cas où "list_folder_and_kml_paths" est vide)
        if list_folder_and_kml_paths:
            #kml en csv
            list_new_csv = []
            for flight_leg_kml in list_folder_and_kml_paths:
                csv_tentative = kml_to_csv.fct_kml_2_csv(flight_leg_kml)
                #on génère tout mais on ne continue que si l'avion a volé. Parfois, ils n'ont qu'une phase au sol (maintenance de l'A/C certainement).
                if csv_tentative != "pas de phase en vol":
                    list_new_csv.append(csv_tentative)

            #idem, on ne continue que si on a des nouveaux vols (ici, des vols qui ont volé ;)
            if list_new_csv:
                #initiatilisation du df

                df_new_flights_empty = pd.DataFrame(columns = df_ac_data.columns)

                #récupération des infos pour tous les nouveaux vols de cet avion
                df_new_flights_only = get_new_df_data.fct_get_all_data(df_new_flights_empty,
                                                                       list_new_csv,
                                                                       registration_ac,
                                                                       icao24_ac, co2_ac, ac_proprio)

                # on teste le nouveau df avec les fonctions de consolidations.
                df_new_flights_only = post_flight_consolidation.fct_short_flight(df_new_flights_only)

                #plot map grâce à plotly avec les infos requises pour le titre de l'image
                for new_flight in df_new_flights_only.itertuples():
                    co2_new = new_flight.co2_emission_tonnes
                    tps_vol_new = new_flight.flight_duration_str
                    path_csv_flight = new_flight.path_csv
                    date_map = new_flight.departure_date_only_utc_map.strftime("%#d %B %Y")

                    csv_to_map.fct_csv_2_map(path_csv_flight, registration_ac, date_map, co2_new, tps_vol_new, ac_proprio)


                # #clean and save data
                #on nettoie new flight avant de le fusionner
                df_new_flights_only = df_new_flights_only.drop(columns=["departure_date_only_utc_map"])

                #une fois fini on regroupe tous les vols.
                #Pas de check de duplicate car protection dans "fct_kml_2_folder" et dans la gestion de la date de dernier check dans df_avion. Peut être amélioré
                df_complete = pd.concat([df_ac_data, df_new_flights_only])
                df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending = False)

                # on teste le nouveau df complet avec les fonctions de consolidations.
                #☺ df complet car il faut le vol n-1 pour compléter.
                df_complete = post_flight_consolidation.fct_airport_vs_cruise(df_complete)

                # on met à jour la date de dernier check.
                df_avion.loc[df_avion["registration"] == registration_ac, "last_check"] = today_date.date()

                #puis on sauvegarde
                df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")
                df_avion.to_csv(path_avions, index=False, encoding="utf-8-sig")

                n = n + len(df_new_flights_only)
                print()
                print(f"--- {registration_ac} done ! ---")
                print("---------------------------")


            else:
                # malgré tout, on met à jour la date de dernier check.
                df_avion.loc[df_avion["registration"] == registration_ac, "last_check"] = today_date.date()
                df_avion.to_csv(path_avions, index=False, encoding="utf-8-sig")
                print(f"--- No new flights for A/C {registration_ac} ---")
                print(f"--- {registration_ac} done ! ---")

        else:
            # malgré tout, on met à jour la date de dernier check.
            df_avion.loc[df_avion["registration"] == registration_ac, "last_check"] = today_date.date()
            df_avion.to_csv(path_avions, index=False, encoding="utf-8-sig")
            print(f"--- No new flights for A/C {registration_ac} ---")
            print(f"--- {registration_ac} done ! ---")

    else:
        # malgré tout, on met à jour la date de dernier check.
        df_avion.loc[df_avion["registration"] == registration_ac, "last_check"] = today_date.date()
        df_avion.to_csv(path_avions, index=False, encoding="utf-8-sig")
        print(f"--- No new flights for A/C {registration_ac} ---")
        print(f"--- {registration_ac} done ! ---")


#%%
print()
print("---------------------------")
print("--- all aircraft done ! ---")
print(f"--- Il y a eu {str(n)} nouveau(x) vol(s) généré(s) ---")


#%% concat all aircraft df in one csv
post_flight_consolidation.fct_concat_all_flights(df_avion, path)


#%%
print(f"--- temps d'execution {round((time.time() - start_time)/60.0,1)} minutes ---")
print("---")