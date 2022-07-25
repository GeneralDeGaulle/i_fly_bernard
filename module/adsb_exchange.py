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

import os


#%%
def fct_adsbex_check_new_flights_and_kml(icao, regis, path_f_data, last_check_d):
    #définir profile firefox, surtout pour configurer le lieu d'enregistrement du fichier et le non-clic pour démarrer le téléchargement
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", path_f_data)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

    #ouvre firefox
    browser = webdriver.Firefox(firefox_profile=profile, executable_path=GeckoDriverManager().install())
    print(),print()

    #définir les dates de vérification (dernier check de l'avion (enregistré dans le fichier avions.csv) et aujourd'hui)
    today_date = pd.to_datetime("now", utc=True)
    diff_nb_jours = (today_date - last_check_d).days

    list_new_flights_legs = []
    #on commence de 0 pour le cas où on relance le programme plusieurs fois par jour
    for i in range(0, diff_nb_jours + 1):
        tested_date = str((last_check_d + dt.timedelta(i)).date())
        url = "https://globe.adsbexchange.com/?icao=" + icao + "&showTrace=" + tested_date

        #A noter que l'url du site est parfaite pour nous permettre de faire tourner les dates les unes après les autres
        browser.get(url)
        time.sleep(1) #to be sure to load the data

        #commande classique soup
        content = browser.page_source
        soup = BeautifulSoup(content, "html.parser")

        #on charge deux éléments spécifiques de la page qui nous permettent de savoir s'il y a un nouveau vol ou non à cette date
        soup_item_to_check_flight = soup.find("div",attrs={"class":"identSmall","id":"leg_sel"}).get_text()
        soup_item_to_check_flight_2 = soup.find("span",attrs={"id":"selected_pos_epoch"}).get_text()
        today_time_epoch = today_date.timestamp() #on calcule le timestamp ici car si on le prend hors de la boucle for, on pourrait bêtement emplafonner le seuil plus bas s'il y a bcp de jours à tester

        #no flight data this day
        if soup_item_to_check_flight == ("No Data available for\n" + tested_date):
            print("--- " + tested_date + ": no flight found for A/C " + regis + " ---")

        #pour ne pas traiter les vols encore en cours. le choix 60s est arbitraire
        elif abs(today_date.timestamp() - float(soup_item_to_check_flight_2)) < 60:
            print("--- " + tested_date + ": A/C "+ regis + " still in flight ---")

        #protection against strange old flights
        elif soup_item_to_check_flight == "Legs: All" and soup_item_to_check_flight_2 == "NaN":
            print("--- " + tested_date + ": no flight found for A/C " + regis + " ---")

        #enfin, c'est un nouveau vol que l'on peut traiter
        elif soup_item_to_check_flight == "Legs: All" and soup_item_to_check_flight_2 != "NaN":

            #on définit le chemin du future fichier qui sera le meme pour tous les legs du jour
            path_kml = os.path.join(path_f_data, regis + "-track-press_alt_uncorrected.kml")

            #on clique sur le bouton "précédent leg" pour aller en arrière et avoir directement le dernier leg du jour.
            click_previous_leg = browser.find_element(By.ID,"leg_prev")
            click_previous_leg.click()
            #on laisse un peu de temps juste au cas où
            time.sleep(0.5)

            #on réactulise soup après cet appui bouton
            content = browser.page_source
            soup = BeautifulSoup(content, "html.parser")
            soup_last_leg_nb_str = soup.find("div",attrs={"class":"identSmall","id":"leg_sel"}).get_text()
            nb_leg_int = int(soup_last_leg_nb_str.replace("Leg: ", ""))

            #pour chaque leg, on va télécharger le kml et le nommer correctement
            #façon facile de rembobiner le bon nombre de legs, meme quand leg = 1
            for i in range(nb_leg_int,0,-1):
                #on télécharge le fichier
                download_kml = browser.find_element_by_xpath("//button[text()='uncorrected pressure alt.']")
                download_kml.click()
                time.sleep(0.5)


                #protection pour que le fichier télécharge complètement avant de passer à la suite
                n = 0
                while not os.path.exists(path_kml) or os.path.getsize(path_kml) <= 3000:
                    n = n+1
                    time.sleep(1)
                    print("!!! en attente du téléchargement fichier !!!!")
                    #pour couvrir les petits vols tout en évitant les problèmes timing, on attend 5s avant de passer à la suite
                    if n == 5 and os.path.exists(path_kml):
                        print("--- petit vol ---")
                        break

                #on renomme pour le cas où plusieurs legs par jour (pour éviter d'écraser les précédents fichiers avec le même nom générique d'adsb-exchange)
                path_kml_leg_i = os.path.join(path_f_data, f"{regis}_baro_{tested_date}_leg_{str(i)}.kml")
                os.rename(path_kml, path_kml_leg_i)

                #on sauve les path des fichiers kml et les infos pour faciliter la function suivante dans "c_kml_to_csv.py"
                list_new_flights_legs.append([regis, tested_date, path_kml_leg_i, "leg_" + str(i), i])

                #on clique sur le précédent pour préparer la prochaine boucle et passer au prochain leg
                click_previous_leg = browser.find_element(By.ID,"leg_prev")
                click_previous_leg.click()
                time.sleep(0.5)


            print(f"--- {tested_date}: {str(nb_leg_int)} new flight(s) found for A/C {regis} ---")


        else:
            print()
            print(f"!!!  EROOR for {tested_date} and {regis} !!!")
            print()

    # on pourrait se poser la question de savoir s'il ne serait pas plus judicieux de fermer firefox une fois tous les avions faits
    # (et non pas comme ici pour un seul avion).Cela pose plusieurs problèmes et notamment le fait de ne pas pouvoir télécharger
    # les kml au bon endroit pour chaque avion (voir commentaire plus haut). Rien d'insurmontable mais bon, ça marche pour l'intant
    browser.quit()

    return list_new_flights_legs








