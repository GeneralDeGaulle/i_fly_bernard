# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 13:05:02 2022

Travail de génération manuel principalement

@author: GeneralDeGaulle
"""

#%% import library
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot #for displaying picture in spyder/browser

import os

import locale
locale.setlocale(locale.LC_TIME,"")


#%%
# import glob
# list_files = glob.glob(path_flight_data + "**/*.csv", recursive = True)


#%% path
path = os.getcwd()

path_avions = os.path.join(path, r"input\avions.csv")
path_output_bilan = os.path.join(path, r"\output\Bilans")


#%%
df_avion = pd.read_csv(path_avions, delimiter = ",")

list_ac = df_avion["registration"].values


#%% create full df
df_all_flights = pd.DataFrame()

for ac in list_ac:
    path_ac = os.path.join(path, "output", ac, ac +"_flight_data_all.csv")
    df = pd.read_csv(path_ac, delimiter = ",")
    df_all_flights = pd.concat([df_all_flights, df])


df_all_flights["departure_date_utc"] = pd.to_datetime(df_all_flights["departure_date_utc"], utc=True)
df_all_flights["arrival_date_utc"] = pd.to_datetime(df_all_flights["arrival_date_utc"], utc=True)
df_all_flights = df_all_flights.sort_values(by=["departure_date_utc"], ascending = False)
df_all_flights = df_all_flights.reset_index(drop=True)

df_all_flights["routes"] = df_all_flights["airport_departure"] + " - " + df_all_flights["airport_arrival"]
df_all_flights["routes"] = df_all_flights["routes"].astype('category')

list_colonnes = df_all_flights.columns.tolist()

for aircraft in list_ac:
    nom = df_avion[df_avion["registration"] == aircraft].proprio.values[0]
    df_all_flights.loc[df_all_flights["registration"] == aircraft, "propriétaire"] = nom

#pour mettre le propriétaire en premier
df_all_flights = df_all_flights.loc[:,["propriétaire" ] + list_colonnes]

path_all_ac = os.path.join(path, "output", "all_flights_data.csv")
df_all_flights.to_csv(path_all_ac, index=False, encoding="utf-8-sig")


#%% filtre temporel
date_1 = pd.to_datetime("01-07-2022", utc=True, dayfirst=True)
date_2 = pd.to_datetime("01-08-2022", utc=True, dayfirst=True)

df_all_flights_m = df_all_flights.loc[(df_all_flights["departure_date_utc"] >= date_1) & (df_all_flights["departure_date_utc"] < date_2)]


#%% stats mensuel tout
save_stat = []

df_all_flights_m_agg = df_all_flights_m[["flight_duration_min","co2_emission_tonnes"]].agg(["count", "sum", "mean", "min", "max"]).round(1)
df_all_flights_m_rte =str( df_all_flights_m["routes"].describe())

print(df_all_flights_m_agg.to_markdown(tablefmt="fancy_grid"))
print(df_all_flights_m_rte)


save_stat.append("--- All flights ---")
save_stat.append(df_all_flights_m_agg.to_markdown(tablefmt="fancy_grid") + "\n")
save_stat.append(df_all_flights_m_rte)
save_stat.append("------------------------------------------------\n\n")


#%% stats mensuels avion
df_all_flights_m_grouped = df_all_flights_m.groupby("registration").sum()
df_all_flights_m_grouped = df_all_flights_m_grouped[["flight_duration_min", "co2_emission_tonnes"]].sort_values(by=["flight_duration_min"], ascending = False).reset_index()

# df_all_flights_m_grouped["flight_duration_min"] = df_all_flights_m_grouped["flight_duration_min"].apply(lambda x: maths_for_map.fct_time_str(x))

print(df_all_flights_m_grouped.to_markdown(tablefmt="fancy_grid"))

save_stat.append("--- Pour chaque avion ---")
save_stat.append(df_all_flights_m_grouped.to_markdown(tablefmt="fancy_grid") + "\n")
save_stat.append("------------------------------------------------\n\n")


#%% Stats détaillées pour chaque avion
for ac in list_ac:
    df = df_all_flights_m[df_all_flights_m["registration"] == ac]

    agg = df[["flight_duration_min","co2_emission_tonnes"]].agg(["count", "sum", "mean", "min", "max"])
    rte = str(df["routes"].describe())

    save_stat.append("--- " + ac +" ---")
    save_stat.append(agg.to_markdown(tablefmt="fancy_grid") + "\n")
    save_stat.append(rte)
    save_stat.append("------------------------------------------------\n\n")


#%% file save
output_file_3 = open(path_output_bilan + r"\bilans_" + date_1.strftime("%B_%Y")  + ".csv", 'w', encoding="utf-8-sig")
text_new_3 = "\n".join(save_stat)
output_file_3.write(text_new_3)
output_file_3.close()




#%% color
for aircraft in df_all_flights_m["registration"].unique():
    print(aircraft)
    nom = df_avion[df_avion["registration"] == aircraft].proprio.values[0]
    print(nom)
    df_all_flights_m.loc[df_all_flights_m["registration"] == aircraft, "nom"] = nom

# df_fgvma_m["ac_color"] = px.colors.qualitative.Pastel[0]
# df_fhfhp_m["ac_color"] = px.colors.qualitative.Pastel[1]
# df_fgbol_m["ac_color"] = px.colors.qualitative.Pastel[2]

# df_all_flights_m.loc[df_all_flights_m["registration"] == "F-GVMA", "ac_color"] = px.colors.qualitative.Pastel[0]
# df_all_flights_m.loc[df_all_flights_m["registration"] == "F-GBOL", "ac_color"] = px.colors.qualitative.Pastel[1]
# df_all_flights_m.loc[df_all_flights_m["registration"] == "F-HFHP", "ac_color"] = px.colors.qualitative.Pastel[2]



#%%
df = df_all_flights_m
df_markers = df[(df["airport_departure"] != "A/C in cruise") & (df["airport_arrival"] != "A/C in cruise")]

fig = px.line_geo(df, lat = "latitude_dep", lon = "longitude_dep",
                  color = "nom", color_discrete_sequence = px.colors.qualitative.Pastel, #Vivid
                  markers = False) #on met false pour que le marker aeroport n'apparqasse pas dans la legend

#pour compenser px...
fig.data[0].opacity = 0.65
for trace in fig.data:
    trace.line.width = 3


fig.update_geos(projection_type  = "natural earth", #scope= "europe",
                showland = True, landcolor = "#f3f3f3",
                showcountries = True, countrycolor = "rgb(204, 204, 204)", #rgb(243, 243, 243)
                showlakes = False,
                showocean = True, oceancolor = "#161a1d", #px.colors.qualitative.Pastel1[1],
                fitbounds="locations")#B1E2FF


#et donc on trace a part les marker
# fig.add_trace(go.Scattergeo(
#         lon = df_markers["longitude_dep"], lat = df_markers["latitude_dep"],
#         mode = 'markers', marker_size = 6.5, marker_color = "silver", marker_line_color = "grey", marker_line_width = 0.5,
#         showlegend = False))


fig.update_layout(font_family="Segoe UI Semibold")
fig.update_layout(legend_title="<b> Propriétaire du jet privé", legend_font_size=15, legend_font_color ="#161a1d",
                  legend=dict(xanchor="left", x=0.12, yanchor="top", y=0.80))

fig.update_layout(title = "<b>Carte de tous les vols du mois de juillet 2022</b>", title_font_size=25,
                  title_font_color="#f3f3f3", title_x=0.05, title_y = 0.90)

fig.update_layout(margin={"t":0,"r":0, "l":0,"b":0})


plot(fig)


#%%
path_html = path_output + r"\bilans_" + date_1.strftime("%B_%Y")  + ".html"
fig.write_html(path_html)



#%%


#%%
# =============================================================================
# #%% total stat & routes
# =============================================================================
total_flight_time_fgvma_hours = df_fgvma["flight_duration_min"].sum()/60.0
total_flight_time_fhfhp_hours = df_fhfhp["flight_duration_min"].sum()/60.0
total_flight_time_fgbol_hours = df_fgbol["flight_duration_min"].sum()/60.0

#total_fight_time_all = df_all_flights["flight_duration_min"].sum()

total_co2_fgvma_tonne = df_fgvma["co2_emission_kg"].sum()
total_co2_fhfhp_tonne = df_fhfhp["co2_emission_kg"].sum()
total_co2_fgbol_tonne = df_fgbol["co2_emission_kg"].sum()

#%% total stat
df_fgvma["flight_duration_min"].mean()
df_fgvma["flight_duration_min"].min()
df_fgvma[df_fgvma["flight_duration_min"] == df_fgvma["flight_duration_min"].min()].values
df_fgvma["routes"].value_counts()

df_fgbol["flight_duration_min"].mean()
df_fgbol["flight_duration_min"].min()
df_fgbol[df_fgbol["flight_duration_min"] == df_fgbol["flight_duration_min"].min()].values
df_fgbol["routes"].value_counts()

df_fhfhp["flight_duration_min"].mean()
df_fhfhp["flight_duration_min"].min()
df_fhfhp[df_fhfhp["flight_duration_min"] == df_fhfhp["flight_duration_min"].min()].values
df_fhfhp["routes"].value_counts()


#%%
df_fgvma_brussels = df_fgvma[(df_fgvma["routes"] == "Brussels Airport - Paris-Le Bourget Airport") | (df_fgvma["routes"] == "Paris-Le Bourget Airport - Brussels Airport")]
df_fgvma_brussels[["co2_emission_tonnes","flight_duration_min"]].sum()
df_fgvma_brussels[["co2_emission_tonnes","flight_duration_min"]].describe()

df_fgbol_cornouaille = df_fgbol[(df_fgbol["routes"] == "Quimper-Cornouaille Airport - Paris-Le Bourget Airport") | (df_fgbol["routes"] == "Paris-Le Bourget Airport - Quimper-Cornouaille Airport")]
df_fgbol_cornouaille[["co2_emission_tonnes","flight_duration_min"]].sum()
df_fgbol_cornouaille[["co2_emission_tonnes","flight_duration_min"]].describe()

#%%

