# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 20:26:30 2022

script offline et séparé des autres, qui sert à générer des plots spécifiques (par exemple pour
twitter un cas où il y a eu 3 vols par jour ou un autre concernant un tour du monde)

@author: GeneralDeGaulle
"""

# https://plotly.com/python/builtin-colorscales/
# https://plotly.com/python/discrete-color/
# https://stackoverflow.com/questions/72496150/user-friendly-names-for-plotly-css-colors
# https://seaborn.pydata.org/tutorial/color_palettes.html

#%%
import pandas as pd
import os
import math

import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot  # for displaying picture in spyder/browser

import locale

locale.setlocale(locale.LC_TIME, "")


#%% script
from src.core import maths_for_bernard


#%% path
path = os.getcwd()

path_all_flights = os.path.join(path, "output", "all_flights_data.csv")


#%% load df
df_all_flights = pd.read_csv(path_all_flights, delimiter=",")
df_all_flights["departure_date_utc"] = pd.to_datetime(    df_all_flights["departure_date_utc"], utc=True, format="%Y-%m-%d %H:%M:%S")
df_all_flights["arrival_date_utc"] = pd.to_datetime(df_all_flights["arrival_date_utc"], utc=True, format="%Y-%m-%d %H:%M:%S")

df_all_flights = df_all_flights.sort_values(by="departure_date_utc")


#%% filter data
df_filter = df_all_flights[df_all_flights["departure_date_only_utc"] == "2022-08-30"]
df_filter = df_filter[df_filter["propriétaire"] == "avion de location Valljet"]

list_avions = list(df_filter.registration.unique())


#%% prepa données
flight_temps = df_filter["flight_duration_min"].sum()
part_entiere = math.floor(flight_temps / 60.0)
part_decimal = int(round(flight_temps - part_entiere * 60.0, 0))

flight_temps_str = str(math.floor(flight_temps / 60.0)) + "h" + str(part_decimal) + "min"

co2_tot = df_filter["co2_emission_tonnes"].sum()


#%% couleur
n_colors = len(list_avions)
colors = px.colors.sample_colorscale("sunset", [n / (n_colors - 1) for n in range(n_colors)])


df_filter["color_avion"] = ""

for i, ac in enumerate(list_avions):
    df_filter.loc[df_filter["registration"] == ac, "color_avion"] = colors[i]


#%% multiple flights in same day
fig = go.Figure()
for ac in list_avions:
    df_filter_ac = df_filter[df_filter["registration"] == ac]
    n = len(df_filter_ac)
    m = 0
    for i, flight in df_filter_ac.iterrows():

        date_map = flight.departure_date_utc.strftime("%d %B %Y")
        arpt_dep = flight.airport_departure.replace(" Airport", "").replace(" International", "")
        arpt_arr = flight.airport_arrival.replace(" Airport", "").replace(" International", "")
        regis = flight.registration

        legend_i = f"{regis} - vol #{str(m+1)} - {arpt_dep} --> {arpt_arr}"

        df = pd.read_csv(flight.path_csv)
        geo_lat, geo_lon = maths_for_bernard.fct_geodesic_multiple_flights(df)

        # trajectoire extrapolée
        fig.add_trace(
            go.Scattermapbox(
                lon=geo_lon,
                lat=geo_lat,
                mode="lines",
                line_width=4,
                line_color=flight.color_avion,
                name=legend_i))

        ## trajectoire réelle
        # fig.add_trace(go.Scattermapbox(lon = df.long, lat = df.lat, mode = "markers",
        #                                     marker_size = 4, marker_color = flight.color_avion,
        #                                     name = legend_i))

        m = m + 1

# fig.update_traces(marker={"size": 5.5})
fig.update_coloraxes(showscale=False)
fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    showlegend=True,
    width=1600,
    height=800,
    mapbox_zoom=3,
    mapbox_style="carto-positron",
    title_text=(f"<b>Tous les vols du {date_map} de la compagnie de location de jets privés Valljet
                </b><br>Total: {flight_temps_str} de vol - {str(co2_tot)} t de CO2 <b>"),
    title_font_family="Arial",
    title_font_size=25,
    title_x=0.5,
    title_y=0.96)

fig.update_layout(
    legend_font_size=10,
    legend_borderwidth=1,
    legend_bordercolor="grey",
    legend_title=f"Vol de la journée du {date_map} - Flotte Valljet",
    legend_title_font_size=12,
    legend=dict(xanchor="left", x=0.01, yanchor="top", y=0.92))

plot(fig)

fig.write_html(df_filter.path_csv.iloc[-1] + "_all_flights.html")


#%%
