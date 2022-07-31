# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 13:23:43 2022

Script #3 qui déplace transforme le kml téléchargé à l'étape d'avant puis le transforme en csv.

@author: GeneralDeGaulle
"""

#%%
from bs4 import BeautifulSoup
import csv
import os


#%%
def fct_kml_2_folder(flights_legs_list_new, path_f_data):

    list_folder_and_kml_paths = []

    # pour chaque vol trouvé et avec kml enregistré
    for flight_leg in flights_legs_list_new:
        # création des différents paths et noms
        path_flight_leg_folder = os.path.join(path_f_data, flight_leg[1], flight_leg[3])
        old_path_kml = flight_leg[2]

        kml_file_name = os.path.basename(old_path_kml)
        new_path_kml = os.path.join(path_flight_leg_folder, kml_file_name)

        file_name_only = os.path.splitext(kml_file_name)[0]

        #crée toute l'arbo (flight_date+leg et si existe ne fait rien)
        os.makedirs(path_flight_leg_folder, exist_ok=True)

        # protection au cas où on a lancer le programme plusieurs fois par jour,
        # on vérifie que le dossier avec les fichiers n'existe pas déjà à l'endroit supposé
        if not os.listdir(path_flight_leg_folder):
            #on coupe/colle le fichier à la bonne place
            os.replace(old_path_kml, new_path_kml)

            #on sauve les path des fichiers kml et les infos pour faciliter la function suivante "fct_kml_2_csv" dans "c_kml_to_csv.py"
            list_folder_and_kml_paths.append([path_flight_leg_folder, new_path_kml, file_name_only])

        # sinon, on supprime le kml et on ne traite pas ce vol
        else:
            os.remove(old_path_kml)
            print(f"--- {file_name_only} already exists ---")


    # print("--- all csv moved in new folders ---")


    return list_folder_and_kml_paths


#%%
def fct_kml_2_csv(flight_leg_kml):

    # on récupère facilement les infos car les i/o entre fct ont été bien faites
    flight_leg_folder = flight_leg_kml[0]
    path_kml = flight_leg_kml[1]
    file_name = flight_leg_kml[2]

    #le csv sera au même endroit que le kml
    path_csv = os.path.join(flight_leg_folder, file_name + ".csv")

    #on ouvre le kml et on va le parcourir avec soup
    f =  open(path_kml, 'r')
    kml_soup = BeautifulSoup(f, 'xml')

    #on prépare le fichier csv
    list_llet = [["long","lat","elevation","time"]]

    #on va parcourir le kml
    for track in kml_soup.find_all('gx:Track'):
        list_llet_i =[]
        #on ne garde que la partie vol du fichier kml, sinon on ne garde pas.
        if track.find("extrude").contents[0] == "1":
            leg_and_ground_when = track.find_all("when")
            leg_and_ground_coord = track.find_all("gx:coord")

            #on récupère les coordonnées long, lat, elev
            for coord in leg_and_ground_coord:
                list_llet_i.append(coord.contents[0].split(" "))

            #on regroupe time avec la précedentes liste créée, dans chaque sous liste de llet. Pas simple mais efficace
            for i, time in enumerate(leg_and_ground_when):
                list_llet_i[i].append(time.contents[0])

        #au cas où plusieurs phases de vols coupées dans le même kml, on concatène toutes les listes (e.g. touch and go)
        list_llet = list_llet + list_llet_i

    #check if flight is ground only, alors on ne traite pas le fichier.
    if list_llet == [["long","lat","elevation","time"]]:
        print(f"!!! no flight phase for {file_name} !!!")
        return "pas de phase en vol"

    # sinon, on sauvegarde notre csv et on retourne le path_csv qui sera notre point d'entrée pour "get_new_df_data.py"
    else:
        with open(path_csv, "w", newline="") as g:
            writer = csv.writer(g)
            writer.writerows(list_llet)

        print(f"--- {file_name} csv generated ---")
        return path_csv


#%%