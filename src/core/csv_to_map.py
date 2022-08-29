# -*- coding: utf-8 -*-
"""
Created on Mon Apr  4 20:40:44 2022

Script #5 qui utilise la trajectoire csv et les infos de "d_get_new_df_data.py" pour générer la carte de la trajectoire et/ou le html.
Si absence de données pendant plus de x minutes, calcule de la géodésique pour combler le trou.

@author: GeneralDeGaulle
"""

#https://plotly.com/python/builtin-colorscales/
#https://plotly.com/python/discrete-color/
#https://stackoverflow.com/questions/72496150/user-friendly-names-for-plotly-css-colors

#%%
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot #for displaying picture in spyder/browser
from PIL import Image

import os


#%%
from src.core import maths_for_bernard


#%%
path = os.getcwd()

path_ac_png = os.path.join(path, "input", "airplane_jet.png")


#%%
def fct_csv_2_map(rel_path_flight_csv, regis, date_vol, co2, flight_temps, proprio):

    #normalement, ce n'est pas utile de repasser en absolu car cwd() est bien définit. Mais pour d'autres users github, ça aidera.
    path_flight_csv = os.path.join(path, rel_path_flight_csv)

    df = pd.read_csv(path_flight_csv)
    df["time"] = pd.to_datetime(df["time"], utc=True) #, errors="coerce")

    csv_name = os.path.basename(path_flight_csv)
    file_name_only = os.path.splitext(csv_name)[0]


    # =============================================================================
    # calcul du point moyen de la trajectoir afin de centrer la map sur ce point moyen.
    if len(df) > 2:
        center_index = len(df)//2

        center_lat = df["lat"].iloc[center_index]
        center_long = df["long"].iloc[center_index]

        center_lat_next = df["lat"].iloc[center_index+1]
        center_long_next = df["long"].iloc[center_index+1]

        bearing = maths_for_bernard.fct_get_bearing(center_lat, center_long, center_lat_next, center_long_next)

    #pour éviter les pb si touts petits fichiers...c'est pas très joli et c'est arrivée qu'une fois.
    else:
        center_lat = df["lat"].iloc[0]
        center_long = df["long"].iloc[0]
        bearing = 0


    # =============================================================================
    # on trace la trajectoire normalement
    fig = px.scatter_mapbox(df, lat="lat", lon="long", color="elevation", color_continuous_scale="Temps",# Temps sunset sunsetdark,Plasma_r
                            mapbox_style="carto-positron", #"open-street-map" "stamen-toner"
                            width=800, height=800,
                            zoom=5, # malheuresement, il n'y a pas de fonctio zoom_auto pour contenir toute la trajectoire. 5 est un bonne valeur en moyenne
                            center=dict(lat=center_lat, lon=center_long))

    # define layout, title, etc
    fig.update_traces(marker={"size": 5.5})
    fig.update_coloraxes(showscale=False)
    fig.update_layout(margin = {"r":0,"t":0,"l":0,"b":0}, showlegend = False,
                      title_text = "<b> Vol de l'" + proprio + "</b><br>" + regis + " - " + str(date_vol) + " - " + flight_temps + " de vol - " + str(co2) + "t de CO2 <b>",
                      title_font_family="Arial", title_font_size=25, title_x=0.5, title_y=0.96) #, title_font_color = "darkblue


    # =============================================================================
    # on regarde si dans le csv, deux points consécutifs on un écart de plus de 7min afin de rechercher les trous de trajectoires
    df["diff_time"] = df["time"].shift(-1) - df["time"]
    df["diff_time"] = df["diff_time"].apply(lambda x: x.seconds/60.0)

    df_gaps = df[df["diff_time"] >= 7]

    # si vide, on termine le code
    if df_gaps.empty:
        ### save fig
        path_image = path_flight_csv + ".jpeg"
        fig.write_image(path_image, engine="kaleido")
        # fig.write_html(path_image + ".html")
        # plot(fig)

        ### save fig + on ajoute l'avion sur la trajectoire
        # comme Plotly ne permet pas d'ajouter ces propres images par dessus scatter_mapbox, on le fait avec PIL.
        # l'astuce trouvée est d'avoir positionner le centre de la trajectoire au centre de l'image. donc on a pas besoin de calculer une fonction de transfert lat/long --> pixel.
        # PIL ajoute l'image de l'avion au centre de l'autre image et c'est bon. ça empêche d'être souple mais au moins c'est automatique et ça marche !
        map_img = Image.open(path_image)
        ac_img = Image.open(path_ac_png)
        ac_img = ac_img.rotate(-bearing,resample=Image.BICUBIC) #- because counter clockwise, resamp to no lose quality

        map_ac_img = map_img.copy()
        map_ac_img.paste(ac_img, (400-21, 400-25),ac_img)# -21/-25 pour positionner le centre de l"avion (et pas l"angle en haut à droite)
        map_ac_img.save(path_image, quality=100)
        # map_ac_img.show()


    # ============================================================================
    # si un trou est identifié (ou plusieurs), on complète le graph précédent avec geodesic (graph plotly et pas PIL)
    else:
        center_lat = (df["lat"].iloc[-1] + df["lat"].iloc[0])/2
        center_long = (df["long"].iloc[-1] + df["long"].iloc[0])/2

        fig.update_layout(width=800, height=800, mapbox_zoom=3, mapbox_center=dict(lat=center_lat, lon=center_long))

        for y in range(len(df_gaps)):
            index_gap = df_gaps.index[y]
            geo_lat, geo_lon = maths_for_bernard.fct_geodesic(df, y, index_gap)

            fig.add_trace(go.Scattermapbox(lon = geo_lon, lat = geo_lat, mode = "lines",
                                           line_width = 1, line_color = "dimgrey"))

            ### save fig
            # plot(fig)
            # ici, on ne peut pas ajouter l'image de l'avion car on ne sait plus où est le centre de l'image. Donc il faut le rajouter à la main :(
            path_image = path_flight_csv + ".jpeg"
            # fig.write_image(path_image, engine="kaleido")
            fig.write_html(path_image + ".html")
            #on enregistre le html dans ce cas pour pouvoir adapter la vue à la nouvelle trajectoire. Cela éviter de coder un truc complexe pour le zoom


    # ============================================================================

    return print(f"--- {file_name_only} image generated ---")


#%%
