# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 14:23:37 2022

Script #2 qui scrap le site adsbexchange.com à la recherche de nouveau(x) vol(s).
Si nouveau vol détecté, téléchargement du kml.

@author: GeneralDeGaulle
"""

#%% import library

import pandas as pd
from bs4 import BeautifulSoup
import datetime as dt
import time

from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

import os


#%%
def fct_adsbex_check_new_flights_and_kml(icao, regis, path_f_data, last_check_d):
    # définir profile firefox, surtout pour configurer le lieu d'enregistrement du fichier et le non-clic pour démarrer le téléchargement
    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", path_f_data)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

    service = Service(GeckoDriverManager().install())

    # ouvre firefox
    browser = webdriver.Firefox(service=service, options=options)
    print()

    # définir les dates de vérification (dernier check de l'avion (enregistré dans le fichier
    # avions.csv) et aujourd'hui)
    today_date = pd.to_datetime("now", utc=True)
    diff_nb_jours = (today_date - last_check_d).days

    # pour test
    # last_check_d = pd.to_datetime("2021-10-20", utc=True)
    # tested_date = str(pd.to_datetime("2021-10-20", utc=True).date())

    list_new_flights_legs = []
    # on commence de 0 pour le cas où on relance le programme plusieurs fois par jour
    for i in range(0, diff_nb_jours + 1):
        tested_date = str((last_check_d + dt.timedelta(i)).date())
        url = "https://globe.adsbexchange.com/?icao=" + icao + "&showTrace=" + tested_date

        # A noter que l'url du site est parfaite pour nous permettre de faire tourner
        # les dates les unes après les autres
        browser.get(url)
        time.sleep(1)  # to be sure to load the data

        # commande classique soup
        content = browser.page_source
        soup = BeautifulSoup(content, "html.parser")

        # on charge deux éléments spécifiques de la page qui nous permettent de savoir
        # s'il y a un nouveau vol ou non à cette date
        soup_item_to_check_flight = soup.find(
            "div", attrs={"class": "identSmall", "id": "leg_sel"}).get_text()
        soup_item_to_check_flight_2 = soup.find(
            "span", attrs={"id": "selected_pos_epoch"}).get_text()
        today_time_epoch = (today_date.timestamp())
        # on calcule le timestamp ici car si on le prend hors de la boucle for,
        # on pourrait bêtement emplafonner le seuil plus bas s'il y a bcp de jours à tester

        # no flight data this day
        if soup_item_to_check_flight == ("No Data available for\n" + tested_date):
            print("--- " + tested_date + ": no flight found for A/C " + regis + " ---")

        # pour ne pas traiter les vols encore en cours au moment du check. le choix 60s est arbitraire
        elif abs(today_time_epoch - float(soup_item_to_check_flight_2)) < 60:
            print("--- " + tested_date + ": A/C " + regis + " still in flight ---")

        # cas particulier (bug du site ?) où il n'affiche pas les données alors qu'il y a un vol !
        elif soup_item_to_check_flight == "Legs: All" and soup_item_to_check_flight_2 == "NaN":
            # pour l'afficher, on fait prec/next day et normalement c'est bon
            click_previous_day = browser.find_element(By.ID, "trace_back_1d")
            click_previous_day.click()
            time.sleep(0.5)
            click_next_day = browser.find_element(By.ID, "trace_jump_1d")
            click_next_day.click()
            time.sleep(0.5)

            # on réactulise soup après ces appuis bouton
            content = browser.page_source
            soup = BeautifulSoup(content, "html.parser")
            soup_item_to_check_flight = soup.find(
                "div", attrs={"class": "identSmall", "id": "leg_sel"}).get_text()
            soup_item_to_check_flight_2 = soup.find(
                "span", attrs={"id": "selected_pos_epoch"}).get_text()

            if soup_item_to_check_flight == "Legs: All" and soup_item_to_check_flight_2 != "NaN":
                print("--- new epoch=NaN check ---")
                fct_get_kml_from_leg(
                    path_f_data, regis, tested_date, list_new_flights_legs, browser)
            else:
                print(
                    "--- "
                    + tested_date
                    + ": no flight found for A/C "
                    + regis
                    + " with epoch=NaN ---")

        # enfin, c'est un nouveau vol que l'on peut traiter
        elif soup_item_to_check_flight == "Legs: All" and soup_item_to_check_flight_2 != "NaN":
            fct_get_kml_from_leg(path_f_data, regis, tested_date, list_new_flights_legs, browser)

        else:
            print()
            print(f"!!!  ERROR for {tested_date} and {regis} !!!")
            print()

    # on pourrait se poser la question de savoir s'il ne serait pas plus judicieux de fermer firefox une fois tous les avions faits
    # (et non pas comme ici pour un seul avion).Cela pose plusieurs problèmes et notamment le fait de ne pas pouvoir télécharger
    # les kml au bon endroit pour chaque avion (voir commentaire plus haut). Rien d'insurmontable mais bon, ça marche pour l'intant
    browser.quit()

    return list_new_flights_legs


#%%
def fct_get_kml_from_leg(path_flt_data, reg, date_tested, list_new_flt_legs, brwsr):
    # on définit le chemin du future fichier qui sera le meme pour tous les legs du jour
    path_kml = os.path.join(path_flt_data, f"{reg}-track-press_alt_uncorrected.kml")

    # on clique sur le bouton "précédent leg" pour aller en arrière et avoir directement le dernier leg du jour.
    click_previous_leg = brwsr.find_element(By.ID, "leg_prev")
    click_previous_leg.click()
    # on laisse un peu de temps juste au cas où
    time.sleep(0.5)

    # on réactulise soup après cet appui bouton
    content = brwsr.page_source
    soup = BeautifulSoup(content, "html.parser")
    soup_last_leg_nb_str = soup.find(
        "div", attrs={"class": "identSmall", "id": "leg_sel"}
    ).get_text()
    nb_leg_int = int(soup_last_leg_nb_str.replace("Leg: ", ""))

    # pour chaque leg, on va télécharger le kml et le nommer correctement
    # façon facile de rembobiner le bon nombre de legs, meme quand leg = 1
    for i in range(nb_leg_int, 0, -1):
        # on télécharge le fichier
        download_kml = brwsr.find_element("xpath", "//button[text()='uncorrected pressure alt.']")
        download_kml.click()
        time.sleep(0.5)

        # protection pour que le fichier télécharge complètement avant de passer à la suite
        n = 0
        while not os.path.exists(path_kml) or os.path.getsize(path_kml) <= 3000:
            n = n + 1
            time.sleep(1)
            print("!!! en attente du téléchargement fichier !!!!")
            # pour couvrir les petits vols tout en évitant les problèmes timing, on attend 5s avant de passer à la suite
            if n == 2 and os.path.exists(path_kml):
                print("--- petit vol ---")
                break

        # on renomme pour le cas où plusieurs legs par jour (pour éviter d'écraser les précédents fichiers avec le même nom générique d'adsb-exchange)
        path_kml_leg_i = os.path.join(path_flt_data, f"{reg}_baro_{date_tested}_leg_{str(i)}.kml")
        os.rename(path_kml, path_kml_leg_i)

        # on sauve les path des fichiers kml et les infos pour faciliter la function suivante dans "c_kml_to_csv.py"
        list_new_flt_legs.append([reg, date_tested, path_kml_leg_i, "leg_" + str(i), i])

        # on clique sur le précédent pour préparer la prochaine boucle et passer au prochain leg
        click_previous_leg = brwsr.find_element(By.ID, "leg_prev")
        click_previous_leg.click()
        time.sleep(0.5)

    print(f"--- {date_tested}: {str(nb_leg_int)} new flight(s) found for A/C {reg} ---")

    return None


#%%
