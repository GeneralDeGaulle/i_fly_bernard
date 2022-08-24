# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 18:52:22 2022

Script #6 qui contient des fonctions mathématiques utilisées dans les autres scripts (surtout pour "csv_to_map.py").

@author: GeneralDeGaulle
"""
#%%
import pandas as pd
import numpy as np
import math
from geographiclib.geodesic import Geodesic


#%%
# fonction pour déterminer le bearing de l'avion et donc positionner son nez dans le bon sens sur l'image de la trajectoire
# geographiclib.geodesic aurait pu être utilisée
def fct_get_bearing(lat1, long1, lat2, long2):
    diff_long = (long2 - long1)

    x = math.cos(math.radians(lat2)) * math.sin(math.radians(diff_long))
    y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(diff_long))

    bearing_rad = np.arctan2(x,y)
    bearing_deg = np.degrees(bearing_rad)

    return bearing_deg


#%% fonction pour combler les trous de trajectoire entre deux points
def fct_geodesic(df, y, index_gap):
    lat_ini = df["lat"].iloc[index_gap]
    long_ini = df["long"].iloc[index_gap]

    lat_last = df["lat"].iloc[index_gap + 1]
    long_last = df["long"].iloc[index_gap + 1]

    geod = Geodesic.WGS84  # define the WGS84 ellipsoid

    l = geod.InverseLine(lat_ini, long_ini, lat_last, long_last,
        Geodesic.LATITUDE | Geodesic.LONGITUDE)

    n = int(math.ceil(l.a13))

    lat_geo = [l.ArcPosition(i, Geodesic.LATITUDE | Geodesic.LONGITUDE | Geodesic.LONG_UNROLL)["lat2"] for i in range(n)]
    lon_geo = [l.ArcPosition(i, Geodesic.LATITUDE | Geodesic.LONGITUDE | Geodesic.LONG_UNROLL)["lon2"] for i in range(n)]

    return lat_geo, lon_geo


#%% idem mais un peu modifier pour l'autre script
def fct_geodesic_multiple_flights(df):

    lat_ini = df["lat"].iloc[0]
    long_ini = df["long"].iloc[0]

    lat_last = df["lat"].iloc[-1]
    long_last = df["long"].iloc[-1]

    geod = Geodesic.WGS84  # define the WGS84 ellipsoid

    l = geod.InverseLine(lat_ini, long_ini, lat_last, long_last,
        Geodesic.LATITUDE | Geodesic.LONGITUDE)

    n = int(math.ceil(l.a13))


    lat_geo = [l.ArcPosition(i, Geodesic.LATITUDE | Geodesic.LONGITUDE | Geodesic.LONG_UNROLL)["lat2"] for i in range(n)]
    lon_geo = [l.ArcPosition(i, Geodesic.LATITUDE | Geodesic.LONGITUDE | Geodesic.LONG_UNROLL)["lon2"] for i in range(n)]

    return lat_geo, lon_geo


#%% on transforme la durée de vol en format affichable. j'ai pas trouvé plus élégant....
def fct_time_str(flt_duration_min):

    if flt_duration_min >= 60.0:
        part_entiere = math.floor(flt_duration_min/60.0)
        part_decimal = int(round(flt_duration_min - part_entiere*60.0,0))
        if part_decimal >= 10:
            flt_duration_str = str(math.floor(flt_duration_min/60.0)) + "h" + str(part_decimal) +"min"
        else:
            flt_duration_str = str(math.floor(flt_duration_min/60.0)) + "h0" + str(part_decimal) +"min"
    else:
        flt_duration_str = str(int(round(flt_duration_min,0))) +"min"

    return flt_duration_str


#%%