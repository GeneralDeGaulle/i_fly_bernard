# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 20:26:30 2022

script offline et séparé des autres, qui sert à générer des plots spécifiques (par exemple pour
twitter un cas où il y a eu 3 vols par jour ou un autre concernant un tour du monde)

@author: GeneralDeGaulle
"""


#https://plotly.com/python/builtin-colorscales/
#https://plotly.com/python/discrete-color/
#https://stackoverflow.com/questions/72496150/user-friendly-names-for-plotly-css-colors

#%%
import pandas as pd
import os
import math

import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot #for displaying picture in spyder/browser

import locale
locale.setlocale(locale.LC_TIME,"")


#%% script
from src.core import maths_for_bernard


#%%

# =============================================================================
registration_ac = "F-GBOL"
# =============================================================================


#%% define path
path = os.getcwd()
path_avions = os.path.join(path, "input","avions.csv")

path_flight_data = os.path.join(path, "output", registration_ac)
path_flight_data_csv = os.path.join(path_flight_data, f"{registration_ac}_flight_data_all.csv")


#%% load generic data
df_avion = pd.read_csv(path_avions, delimiter = ",")
df_avion["last_check"] = pd.to_datetime(df_avion["last_check"], utc=True)


#%% constant definition et df
df_avion = df_avion[df_avion["registration"] == registration_ac]

icao24_ac = str(df_avion.icao24.values[0])
co2_ac = df_avion.co2_kg_per_hour.values[0]
ac_proprio = df_avion.proprio.values[0]


#%%
df_ac = pd.read_csv(path_flight_data_csv, delimiter = ",")
df_ac["departure_date_utc"] = pd.to_datetime(df_ac["departure_date_utc"], utc=True)
df_ac["arrival_date_utc"] = pd.to_datetime(df_ac["arrival_date_utc"], utc=True)
df_ac["departure_date_only_utc_map"] = pd.to_datetime(df_ac["departure_date_only_utc"])

df_ac = df_ac.head(3)


#%%
flight_temps = df_ac["flight_duration_min"].sum()
part_entiere = math.floor(flight_temps/60.0)
part_decimal = int(round(flight_temps - part_entiere*60.0,0))

flight_temps_str = str(math.floor(flight_temps/60.0)) + "h" + str(part_decimal) +"min"

co2_tot = df_ac["co2_emission_tonnes"].sum()

#%%
# df_ac = df_ac.drop([6,5])
df_ac = df_ac.sort_values(by=["departure_date_utc"], ascending = True)
df_ac = df_ac.reset_index(drop=True)

df_ac["airport_departure"] = ["Paris", "Toulon", "Corfou"]
df_ac["airport_arrival"] = ["Toulon", "Corfou", "Paris"]


#%% couleur contnue difficile car pas bcp de vol
# n_colors = len(df_ac)
# colors_turbo = px.colors.sample_colorscale("reds", [n/(n_colors -1) for n in range(n_colors)])



#%% multiple flights in different day
fig = go.Figure()

for i, flight in df_ac.iterrows():

    date_map = flight.departure_date_only_utc_map.strftime("%d %B %Y")
    legend_i = "vol du " + date_map + " - " + flight.airport_departure + " --> " + flight.airport_arrival


    df = pd.read_csv(flight.path_csv)
    geo_lat, geo_lon = maths_for_bernard.fct_geodesic_multiple_flights(df)

    fig.add_trace(go.Scattermapbox(lon = geo_lon, lat = geo_lat, mode = "lines",
                                       line_width = 6.5, line_color = px.colors.qualitative.Set2[i],
                                       name = legend_i))#colors_turbo[i]


fig.update_coloraxes(showscale=False)
fig.update_layout(margin = {"r":0,"t":0,"l":0,"b":0}, showlegend = True,
                  width=1200, height=800, mapbox_zoom=3, mapbox_style="carto-positron",
                  title_text = "<b>3 vols en 3 jours pour l'" + ac_proprio + "</b><br>" + registration_ac + " - " + flight_temps_str + " de vol - " + str(co2_tot) + "t de CO2 <b>",
                  title_font_family="Arial", title_font_size=25, title_x=0.5, title_y=0.96) #, title_font_color = "darkblue

fig.update_layout(legend_font_size=14, legend_borderwidth = 1, legend_bordercolor = "grey",
                  legend=dict(xanchor="right", x=0.95, yanchor="top", y=0.80))

plot(fig)

fig.write_html(df_ac.path_csv.iloc[-1] + "_all_flights.html")



#%% multiple flights in same day
fig = go.Figure()

for i, flight in df_ac.iterrows():

    date_map = flight.departure_date_only_utc_map.strftime("%d %B %Y")
    depart_time = flight.departure_date_utc.strftime("%Hh%M")
    arrival_time = flight.arrival_date_utc.strftime("%Hh%M")

    legend_i = "vol #" + str(i+1) + " - " + flight.airport_departure + " --> " + flight.airport_arrival + " - " + flight.flight_duration_str


    df = pd.read_csv(flight.path_csv)
    geo_lat, geo_lon = maths_for_bernard.fct_geodesic_multiple_flights(df)

    # trajectoire extrapolée
    fig.add_trace(go.Scattermapbox(lon = geo_lon, lat = geo_lat, mode = "lines",
                                        line_width = 5, line_color = px.colors.qualitative.Pastel[i],
                                        name = legend_i))

    # trajectoire réelle
    # fig.add_trace(go.Scattermapbox(lon = df.long, lat = df.lat, mode = "markers",
    #                                     marker_size = 5.5, marker_color = px.colors.qualitative.Pastel1[i],
    #                                     name = legend_i))


# fig.update_traces(marker={"size": 5.5})
fig.update_coloraxes(showscale=False)
fig.update_layout(margin = {"r":0,"t":0,"l":0,"b":0}, showlegend = True,
                  width=800, height=800, mapbox_zoom=3, mapbox_style="carto-positron",
                  title_text = "<b>Triple vol en seul jour pour l'" + ac_proprio + "</b><br>" + date_map + " - " + registration_ac + " - " + flight_temps_str + " de vol - " + str(co2_tot) + "t de CO2 <b>",
                  title_font_family="Arial", title_font_size=25, title_x=0.5, title_y=0.96) #, title_font_color = "darkblue

fig.update_layout(legend_font_size=14, legend_borderwidth = 1, legend_bordercolor = "grey",
                  legend_title = "Vol de la journée du " + date_map, legend_title_font_size = 16,
                  legend=dict(xanchor="right", x=0.95, yanchor="top", y=0.80))

plot(fig)

fig.write_html(df_ac.path_csv.iloc[-1] + "_all_flights.html")


#%%
# =============================================================================
# code compliqué en dessous pour gérer le vol géant tokyo paris
# =============================================================================
# #%%
# fig = go.Figure()


# for i, flight in df_ac.iterrows():

#     date_map = flight.departure_date_only_utc_map.strftime("%d %B %Y")
#     legend_i = "vol du " + date_map + " - " + flight.airport_departure + " --> " + flight.airport_arrival

#     if not flight.departure_date_only_utc == "2022-07-12":
#         df = pd.read_csv(flight.path_csv)
#         geo_lat, geo_lon = maths_for_bernard.fct_geodesic_multiple_flights(df)

#         fig.add_trace(go.Scattermapbox(lon = geo_lon, lat = geo_lat, mode = "lines",
#                                            line_width = 4, line_color = px.colors.qualitative.Plotly[i],
#                                            name = legend_i))#colors_turbo[i]
#     else:
#         df = pd.read_csv(flight.path_csv)
#         split = len(df)//2
#         df1 = df.iloc[:800]
#         df2 = df.iloc[800:]

#         # geo_lat, geo_lon = maths_for_bernard.fct_geodesic_multiple_flights(df1)
#         # fig.add_trace(go.Scattermapbox(lon = geo_lon, lat = geo_lat, mode = "lines", showlegend = False,
#         #                                    line_width = 4, line_color = px.colors.qualitative.Plotly[i]))#colors_turbo[i]

#         # geo_lat, geo_lon = maths_for_bernard.fct_geodesic_multiple_flights(df2)
#         # fig.add_trace(go.Scattermapbox(lon = geo_lon, lat = geo_lat, mode = "lines",
#         #                                    line_width = 4, line_color = px.colors.qualitative.Plotly[i],
#         #                                    name = legend_i))#colors_turbo[i]

#         fig.add_trace(go.Scattermapbox(lon = [df.long.iloc[0], df.long.iloc[10]], lat = [df.lat.iloc[0], df.lat.iloc[10]],
#                                        mode = "lines", line_width = 4, line_color = px.colors.qualitative.Plotly[i],
#                                        name = legend_i))#colors_turbo[i]

# fig.update_traces(marker={"size": 5.5})
# fig.update_coloraxes(showscale=False)
# fig.update_layout(margin = {"r":0,"t":0,"l":0,"b":0}, showlegend = True,
#                   width=1600, height=800, mapbox_zoom=3, mapbox_style="carto-positron",
#                   title_text = "<b> Tour du monde de l'" + ac_proprio + " en 8 jours </b><br>" + registration_ac + " - " + flight_temps_str + " de vol - " + str(co2_tot) + "t de CO2 <b>",
#                   title_font_family="Arial", title_font_size=25, title_x=0.5, title_y=0.96) #, title_font_color = "darkblue

# fig.update_layout(legend_font_size=12, legend_borderwidth = 1, legend_bordercolor = "grey",
#                   legend=dict(xanchor="left", x=0.68, yanchor="top", y=0.90))


# fig.write_html(df_ac.path_csv[0] + "_all_flights.html")
# plot(fig)


#%%
