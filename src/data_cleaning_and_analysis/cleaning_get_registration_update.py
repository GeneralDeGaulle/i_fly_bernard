# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 17:37:18 2022

Script to get registration file from "https://immat.aviation-civile.gouv.fr/immat/servlet/aeronef_liste.html#"
and update "avions.csv" with it

@author: MPADXUR1
"""

#%% import lib
import pandas as pd
import os


#%% define path
path = os.getcwd()
path_avions = os.path.join(path, "input", "avions.csv")



#%% load df av
df_avion = pd.read_csv(path_avions, delimiter=",")


#%% define url and load dgac file
url = "https://immat.aviation-civile.gouv.fr/immat/servlet/static/upload/export.csv"
df_dgac = pd.read_csv(url, delimiter=";", encoding="unicode_escape")

df_dgac = df_dgac.rename(columns={"ï»¿IMMATRICULATION": "IMMATRICULATION"})

#%% check and update
list_avions = list(df_avion.registration)

df_dgac_ifb = df_dgac[df_dgac.IMMATRICULATION.isin(list_avions)]

check_radiés = df_dgac_ifb[df_dgac_ifb["PROPRIETAIRE"].isna()]
print(check_radiés.IMMATRICULATION)


#%% save df_avion
# df_parameter_list.to_csv(path_output, index = False, encoding = "utf-8-sig")


#%%
