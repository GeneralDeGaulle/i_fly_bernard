# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 21:42:57 2022

@author: GeneralDeGaulle
"""

#%%
import tweepy

#%%
token_access = "1515774132494950401-i4HooHbt3uFw9Na4LMUKKJZG9gtxrc"
token_access_secret = "ZsHCaZLgntDXgrHHrvnPY6C1TGIr7AmxdkNjUhYnqCpla"

API_key = "DAZ7kB3ZwhlNKLwCH7yyiOiqb"
API_key_secret = "aiMFjWeHd9pl2AJyi3JOOmUYYHRpDCMrH4kmomFhkr1Ic2LjkI"


#%%
auth = tweepy.OAuth1UserHandler(API_key, API_key_secret, token_access, token_access_secret)
api = tweepy.API(auth)


#%%
df_all_new_flights_twitter["auto_tweet"] = "yes"


#%%
df_auto_flights_twitter = df_all_new_flights_twitter[df_all_new_flights_twitter["auto_tweet"] == "yes"]


#%% text tweet
list_tweet = []
for flight_tweet in df_auto_flights_twitter.itertuples():
    regis_tweet = flight_tweet.registration
    co2_tweet = flight_tweet.co2_emission_tonnes
    tps_vol_new = flight_tweet.flight_duration_str
    path_csv_tweet = new_flight.path_csv
    date_tweet = flight_tweet.departure_date_only_utc_map.strftime("%#d %B %Y")

    ac_proprio = df_avion[df_avion["registration"] == regis_tweet].proprio.values

    text_tweet = "Auto: Vol de l'" + ac_proprio + " le " + date_tweet + ". " + tps_vol_new + " de temps de vol pour " + str(co2_tweet) + " tonnes de CO2 émis."

    list_tweet.append([text_tweet, path_csv_tweet])


print(list_tweet)

#%%
for tweet in list_tweet:
    media_1 = api.media_upload(filename=tweet[1])
    tweet = api.update_status(status=tweet[0][0], media_ids=[media_1.media_id])


