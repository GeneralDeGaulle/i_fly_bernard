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
from module import post_flight_data_consolidation
from module import maths_for_map


#%%
# import glob
# list_files = glob.glob(path_flight_data + "**/*.csv", recursive = True)


#%% path
path = os.getcwd()

path_avions = os.path.join(path, r"input\avions.csv")
path_all_flights = os.path.join(path, r"output\all_flights_data.csv")
path_output_bilan = os.path.join(path, r"output\Bilans")


#%%
df_avion = pd.read_csv(path_avions, delimiter = ",")
df_avion = df_avion.sort_values(by=["proprio"])

list_ac = df_avion["registration"].values



#%% concat all flights data
post_flight_data_consolidation.fct_concat_all_flights(df_avion, path)
print("--- all_flights_data.csv généré ---")


#%% load df
df_all_flights = pd.read_csv(path_all_flights, delimiter = ",")

df_all_flights["departure_date_utc"] = pd.to_datetime(df_all_flights["departure_date_utc"], utc=True)
df_all_flights["arrival_date_utc"] = pd.to_datetime(df_all_flights["arrival_date_utc"], utc=True)


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

path_csv_all_flights_m_agg = os.path.join(path_output_bilan, "df_all_flights_m_agg" + ".csv")
df_all_flights_m_agg.to_csv(path_csv_all_flights_m_agg, encoding="utf-8-sig")


#%% stats mensuels avion
df_all_flights_m_grouped = df_all_flights_m.groupby("propriétaire").sum()
df_all_flights_m_grouped = df_all_flights_m_grouped[["flight_duration_min", "co2_emission_tonnes"]].sort_values(by=["flight_duration_min"], ascending = False).reset_index()

# df_all_flights_m_grouped["flight_duration_min"] = df_all_flights_m_grouped["flight_duration_min"].apply(lambda x: maths_for_map.fct_time_str(x))

print(df_all_flights_m_grouped.to_markdown(tablefmt="fancy_grid"))

save_stat.append("--- Pour chaque avion ---")
save_stat.append(df_all_flights_m_grouped.to_markdown(tablefmt="fancy_grid") + "\n")
save_stat.append("------------------------------------------------\n\n")

path_all_flights_m_grouped = os.path.join(path_output_bilan, "df_all_flights_m_grouped" + ".csv")
df_all_flights_m_grouped.to_csv(path_all_flights_m_grouped, encoding="utf-8-sig")

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
output_file_3 = open(os.path.join(path_output_bilan, r"bilans_" + date_1.strftime("%B_%Y") + ".txt"), 'w', encoding="utf-8-sig")
text_new_3 = "\n".join(save_stat)
output_file_3.write(text_new_3)
output_file_3.close()


#%% color

# df_fgvma_m["ac_color"] = px.colors.qualitative.Pastel[0]
# df_fhfhp_m["ac_color"] = px.colors.qualitative.Pastel[1]
# df_fgbol_m["ac_color"] = px.colors.qualitative.Pastel[2]

for i, ac in enumerate(list_ac):
    df_all_flights_m.loc[df_all_flights_m["registration"] == ac, "color"] = px.colors.qualitative.Set2[i]


# df_all_flights_m.loc[df_all_flights_m["registration"] == "F-GVMA", "ac_color"] = px.colors.qualitative.Pastel[0]
# df_all_flights_m.loc[df_all_flights_m["registration"] == "F-GBOL", "ac_color"] = px.colors.qualitative.Pastel[1]
# df_all_flights_m.loc[df_all_flights_m["registration"] == "F-HFHP", "ac_color"] = px.colors.qualitative.Pastel[2]


#%% multiple flights per ac
fig = go.Figure()

for n, ac in enumerate(list_ac):
    df_ac = df_all_flights_m[df_all_flights_m["registration"] == ac]
    m = n
    for flight in df_ac.itertuples():


        legend_i = flight.propriétaire
        color_i = flight.color

        df = pd.read_csv(flight.path_csv)
        geo_lat, geo_lon = maths_for_map.fct_geodesic_multiple_flights(df)

        # pour gérer l'affichage d'un seul élément
        print(n, m)
        if m != n:
            fig.add_trace(go.Scattermapbox(lon = geo_lon, lat = geo_lat, mode = "lines",
                                                line_width = 3, line_color = color_i,
                                                name = legend_i, showlegend = False))
        else:
            fig.add_trace(go.Scattermapbox(lon = geo_lon, lat = geo_lat, mode = "lines",
                                                line_width = 3, line_color = color_i,
                                                name = legend_i, showlegend = True))

        m = m + 1

        # #real_trajectory
        # fig.add_trace(go.Scattermapbox(lon = df.long, lat = df.lat, mode = "lines",
        #                                     line_width = 3, line_color = color_i,
        #                                     name = legend_i))


fig.update_coloraxes(showscale=False)

fig.update_layout(margin = {"r":0,"t":0,"l":0,"b":0}, width=1600, height=800,
                  mapbox_zoom=3, mapbox_style="carto-positron")

fig.update_layout(legend_title="<b> Propriétaire du jet privé", legend_font_size=15,
                  legend_font_color ="#161a1d", legend_font_family = "Arial",
                  legend_borderwidth = 1, legend_bordercolor = "grey",
                  legend=dict(xanchor="right", x=0.75, yanchor="top", y=0.75))

fig.update_layout(title = "<b>Carte de tous les vols du mois de juillet 2022</b>",
                  title_font_size=25, title_font_color="#161a1d", title_font_family = "Arial",
                  title_x=0.5, title_y = 0.95)

plot(fig)




#%%
path_html = os.path.join(path_output_bilan, r"bilans_" + date_1.strftime("%B_%Y") + ".html")
fig.write_html(path_html)


#%% old with "not-OSM" map

# df = df_all_flights_m
# df_markers = df[(df["airport_departure"] != "A/C in cruise") & (df["airport_arrival"] != "A/C in cruise")]

# fig = px.line_geo(df, lat = "latitude_dep", lon = "longitude_dep",
#                   color = "propriétaire", color_discrete_sequence = px.colors.qualitative.Pastel, #Vivid
#                   markers = False) #on met false pour que le marker aeroport n'apparqasse pas dans la legend

# #pour compenser px...
# fig.data[0].opacity = 0.65
# for trace in fig.data:
#     trace.line.width = 3


# fig.update_geos(projection_type  = "natural earth", #scope= "europe",
#                 showland = True, landcolor = "#f3f3f3",
#                 showcountries = True, countrycolor = "rgb(204, 204, 204)", #rgb(243, 243, 243)
#                 showlakes = False,
#                 showocean = True, oceancolor = "#161a1d", #px.colors.qualitative.Pastel1[1],
#                 fitbounds="locations")#B1E2FF


# #et donc on trace a part les marker
# # fig.add_trace(go.Scattergeo(
# #         lon = df_markers["longitude_dep"], lat = df_markers["latitude_dep"],
# #         mode = 'markers', marker_size = 6.5, marker_color = "silver", marker_line_color = "grey", marker_line_width = 0.5,
# #         showlegend = False))


# fig.update_layout(font_family="Segoe UI Semibold")
# fig.update_layout(legend_title="<b> Propriétaire du jet privé", legend_font_size=15, legend_font_color ="#161a1d",
#                   legend=dict(xanchor="left", x=0.12, yanchor="top", y=0.80))

# fig.update_layout(title = "<b>Carte de tous les vols du mois de juillet 2022</b>", title_font_size=25,
#                   title_font_color="#f3f3f3", title_x=0.05, title_y = 0.90)

# fig.update_layout(margin={"t":0,"r":0, "l":0,"b":0})


# plot(fig)


