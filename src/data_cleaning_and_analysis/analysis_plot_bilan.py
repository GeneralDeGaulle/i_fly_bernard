# -*- coding: utf-8 -*-
"""
Created on Fri Aug 19 13:05:49 2022

script pour tracer rapidement quelques données avec seaborn (pour changer de plotly ;)

@author: GeneralDeGaulle
"""

#%% import library
import pandas as pd
import seaborn as sns
import os

import matplotlib.pyplot as plt

# https://seaborn.pydata.org/tutorial/color_palettes.html

#%% plt and sns parameters
# plt.rcParams["figure.figsize"] = [7.50, 7.50]
# plt.rcParams["figure.autolayout"] = True

# Apply the default theme
sns.set_theme( palette="pastel", style="whitegrid")


#%% path
path = os.getcwd()

path_all_flights = os.path.join(path, "output", "all_flights_data.csv")


#%% load df
df_all_flights = pd.read_csv(path_all_flights, delimiter = ",")

df_all_flights["departure_date_utc"] = pd.to_datetime(df_all_flights["departure_date_utc"], utc=True)
df_all_flights["arrival_date_utc"] = pd.to_datetime(df_all_flights["arrival_date_utc"], utc=True)

df_all_flights = df_all_flights.sort_values(by = "departure_date_utc")


#%% if needed filtre temporel & avion

# =============================================================================
registration_ac = "F-GVMA"
df_all_flights = df_all_flights[df_all_flights["registration"] == registration_ac]
df_all_flights = df_all_flights[df_all_flights["propriétaire"] == "avion de location Valljet"]
# =============================================================================
date_1 = pd.to_datetime("01-01-2022", utc=True, dayfirst=True)
date_2 = pd.to_datetime("31-08-2022", utc=True, dayfirst=True)

df_all_flights = df_all_flights.loc[(df_all_flights["departure_date_utc"] >= date_1) & (df_all_flights["departure_date_utc"] < date_2)]
# =============================================================================

#%% préparation données
df_all_flights["month"] = df_all_flights['departure_date_utc'].dt.strftime("%b-%Y")
df_all_flights["year"] = df_all_flights['departure_date_utc'].dt.strftime("%Y")
# df_all_flights["trimestre"] = df_all_flights['departure_date_utc'].dt.quarter

df_group_month = df_all_flights.groupby("month", as_index=False, sort = False)["co2_emission_tonnes"].sum()

df_group_month_c = df_all_flights.groupby("month", as_index=False, sort = False)["registration"].count()
df_group_month_c.loc[:,"year"] = df_group_month_c["month"].str.strip().str[4:]

df_group_year = df_all_flights.groupby("year", as_index=False, sort = False)["co2_emission_tonnes"].sum()

df_group_day_c = df_all_flights.groupby("departure_date_only_utc", as_index=False, sort = False)["registration"].count()


df_4month = df_all_flights.groupby(pd.Grouper(key="departure_date_utc", freq="4MS"))[["registration","co2_emission_tonnes"]].count()
df_4month["departure_4month"] = df_4month.index.strftime("%#d%b%Y")
df_4month["departure_4month"] = df_4month["departure_4month"] + "-" + df_4month["departure_4month"].shift(-1)
df_4month["departure_4month"].iloc[-1] = "1Aug2022-21Aug2022"


#%% co2 per year
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=df_group_year, x="year", y="co2_emission_tonnes")#, palette = "Blues_d")

ax.set_xlabel("Année", fontsize = 14)
ax.set_ylabel("Emission de CO2 en tonnes", fontsize = 14)
ax.set_title("Emission de CO2 (en tonnes) par année", fontsize = 16)
ax.tick_params(labelsize=12)
ax.bar_label(ax.containers[0], fontsize = 14)

fig.tight_layout()


plt.show()

#%% nb of flights per 4 month
fig2, ax2 = plt.subplots(figsize=(10, 10))
sns.barplot(data=df_4month, x="departure_4month", y="registration", color="#3498db")#, palette="Blues_d")

ax2.set_xlabel("Période de 4 mois", fontsize = 14)
ax2.set_ylabel("Nombre de vols", fontsize = 14)
ax2.set_title("Nombre de vols par période de 4 mois", fontsize = 16)
ax2.tick_params(labelsize=11, labelrotation=0)
ax2.bar_label(ax2.containers[0], fontsize = 14)

fig2.tight_layout()

plt.show()


#%% nb of flights per month
fig3, ax3 = plt.subplots(figsize=(10, 10))
sns.barplot(data=df_group_month_c, x="month", y="registration", hue="year", dodge=False)

ax3.set_xlabel("Par mois", fontsize = 14)
ax3.set_ylabel("Nombre de vols", fontsize = 14)
ax3.set_title("Nombre de vols par mois", fontsize = 16)
ax3.tick_params(labelsize=10, labelrotation=0)
# ax3.bar_label(ax3.containers[0], fontsize = 11)
# ax3.bar_label(ax3.containers[1], fontsize = 11)

# fig3.tight_layout()


plt.show()

#%% nb of flights per day
fig4, ax4 = plt.subplots(figsize=(10, 10))
sns.barplot(data=df_group_day_c, x="departure_date_only_utc", y="registration")#, hue="year", dodge=False)

ax4.set_xlabel("Par jour", fontsize = 14)
ax4.set_ylabel("Nombre de vols", fontsize = 14)
ax4.set_title("Nombre de vols par jours", fontsize = 16)
ax4.tick_params(labelsize=10, labelrotation=90)
ax4.set_xticks(range(0,240,10))

# fig3.tight_layout()


plt.show()

#%%