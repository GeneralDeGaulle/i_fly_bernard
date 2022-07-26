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

import logging

#pour le format de la date du titre de la carte
import locale
locale.setlocale(locale.LC_TIME,"");


#%% import scripts
from module import adsb_exchange
from module import kml_to_csv
from module import get_new_df_data
from module import csv_to_map

# import map_to_twitter (pour twitter automatiquement, pas utilisé encore)


#%% define path
# path = os.getcwd()
#pour être sûr que le path est le bon au cas où cwd() n'est pas correctement configuré.
path = os.path.dirname(os.path.abspath(__file__))
os.chdir(path)

path_avions = os.path.join(path, r"input\avions.csv")


#%% load generic data
df_avion = pd.read_csv(path_avions, delimiter = ",")
df_avion["last_check"] = pd.to_datetime(df_avion["last_check"], utc=True)

today_date = pd.to_datetime("now", utc=True)


#%% start of loop
n = 0

# #provision pour twitter automatiquement après avoir généré les nouveaux vols.
# df_all_new_flights_twitter = pd.DataFrame()

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

    df_ac_data = pd.read_csv(path_flight_data_csv, delimiter = ",")
    df_ac_data["departure_date_utc"] = pd.to_datetime(df_ac_data["departure_date_utc"], utc=True)
    df_ac_data["arrival_date_utc"] = pd.to_datetime(df_ac_data["arrival_date_utc"], utc=True)
    # df_ac_data = df_ac_data.astype({"co2_emission_kg":"float", "flight_duration_min":"float"})


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
                df_new_flights_only = pd.DataFrame(columns = df_ac_data.columns)

                #pour chaque nouveau vol, et donc chaque csv unique, on se sert du csv pour générer toutes les infos (1ère et dernière positions, temps de vol, CO2 émis, etc)
                for csv_file in list_new_csv:
                    item = get_new_df_data.fct_get_data_from_csv(csv_file, registration_ac, icao24_ac, co2_ac)
                    df_item = pd.DataFrame([item], columns = list(df_ac_data.columns))

                    # on regroupe tous les nouveaux vols du même avions
                    df_new_flights_only = pd.concat([df_new_flights_only, df_item], ignore_index=True)


                #definir types du nouveau df pour simplifier les futures tâches
                df_new_flights_only["departure_date_utc"] = pd.to_datetime(df_new_flights_only["departure_date_utc"])
                df_new_flights_only["arrival_date_utc"] = pd.to_datetime(df_new_flights_only["arrival_date_utc"])
                df_new_flights_only["departure_date_only_utc_map"] = pd.to_datetime(df_new_flights_only["departure_date_only_utc"])#pour map/strftime
                df_new_flights_only = df_new_flights_only.astype({"co2_emission_tonnes":"float", "flight_duration_min":"float","latitude_dep":"float", "longitude_dep":"float","latitude_arr":"float", "longitude_arr":"float"})

                #find airport and add info with lambda and apply (et grâce aux 1ère et dernière positions du csv que l'on a trouvé avec "fct_get_data_from_csv"
                #fonction assez géniale en toute modestie
                df_new_flights_only[["airport_departure","airport_dep_icao"]] = df_new_flights_only.apply(lambda x: get_new_df_data.fct_get_airport_from_lat_lon(x["latitude_dep"], x["longitude_dep"], x["airport_departure"]), axis=1, result_type ="expand")
                df_new_flights_only[["airport_arrival","airport_arr_icao"]] = df_new_flights_only.apply(lambda x: get_new_df_data.fct_get_airport_from_lat_lon(x["latitude_arr"], x["longitude_arr"], x["airport_arrival"]), axis=1, result_type ="expand")


                #plot map grâce à plotly avec les infos requises pour le titre de l'image
                for new_flight in df_new_flights_only.itertuples():
                    co2_new = new_flight.co2_emission_tonnes
                    tps_vol_new = new_flight.flight_duration_str
                    path_csv_flight = new_flight.path_csv
                    date_map = new_flight.departure_date_only_utc_map.strftime("%#d %B %Y")

                    csv_to_map.fct_csv_2_map(path_csv_flight, registration_ac, date_map, co2_new, tps_vol_new, ac_proprio)


                # #provision: on sauvegarde les nouveaux vols pour tweeter pour chaque avion pour twitter
                # df_all_new_flights_twitter = pd.concat([df_all_new_flights_twitter, df_new_flights_only])
                # df_all_new_flights_twitter = df_all_new_flights_twitter.reset_index(drop=True)


                #clean and save data
                #on nettoie new flight avant de le fusionner
                df_new_flights_only = df_new_flights_only.drop(columns=["departure_date_only_utc_map"])

                #une fois fini on regroupe tous les vols.
                #Pas de check de duplicate car protection dans "fct_kml_2_folder" et dans la gestion de la date de dernier check dans df_avion. Peut être amélioré
                df_complete = pd.concat([df_ac_data, df_new_flights_only])
                df_complete = df_complete.sort_values(by=["departure_date_utc"], ascending = False)

                # on met à jour la date de dernier check.
                df_avion.loc[df_avion["registration"] == registration_ac, "last_check"] = today_date.date()

                #puis on sauvegarde
                df_complete.to_csv(path_flight_data_csv, index=False, encoding="utf-8-sig")
                df_avion.to_csv(path_avions, index=False, encoding="utf-8-sig")

                n = n + len(df_new_flights_only)
                print()
                print(f"--- {registration_ac} done ! ---")
                print("---------------------")


            else:
                # malgré tout, on met à jour la date de dernier check.
                df_avion.loc[df_avion["registration"] == registration_ac, "last_check"] = today_date.date()
                df_avion.to_csv(path_avions, index=False, encoding="utf-8-sig")
                print()
                print(f"--- No new flights for A/C {registration_ac} ---")
                print(f"--- {registration_ac} done ! ---")
                print()

        else:
            # malgré tout, on met à jour la date de dernier check.
            df_avion.loc[df_avion["registration"] == registration_ac, "last_check"] = today_date.date()
            df_avion.to_csv(path_avions, index=False, encoding="utf-8-sig")
            print()
            print(f"--- No new flights for A/C {registration_ac} ---")
            print(f"--- {registration_ac} done ! ---")
            print()

    else:
        # malgré tout, on met à jour la date de dernier check.
        df_avion.loc[df_avion["registration"] == registration_ac, "last_check"] = today_date.date()
        df_avion.to_csv(path_avions, index=False, encoding="utf-8-sig")
        print()
        print(f"--- No new flights for A/C {registration_ac} ---")
        print(f"--- {registration_ac} done ! ---")
        print()


#%%
print("---------------------------")
print("--- all aircraft done ! ---")
print(f"--- Il y a eu {str(n)} nouveau(x) vol(s) généré(s) ---")


#%%