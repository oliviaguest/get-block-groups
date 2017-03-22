import os
import csv
import json
import requests

import numpy as np
import pandas as pd
# import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt

from datetime import datetime
from requests.auth import HTTPBasicAuth

# And a dummy state just for now:
state = 'RI'

# After chat with Logan we have discovered the server *probably* times out (we
# can't think of another explanation) when asked to give all the block groups
# for a state (when the state is huge or who knows when...)
# So Logan came up with the following instructions:
# 1) call the citysdk for all counties by state
# 2) get the centroid lat/lng
# 3) use that lat/lng to request:
# 3.a) container: 'county'
# 3.b) sublevel: "block-group"
# This try block gets us the state data one way (disk) or another (interwebs).
request_url = "http://citysdk.commerce.gov"
from secret import *
# apikey = "your_api_key" imported from a file called secret.py in my case
# get your own key here: http://api.census.gov/data/key_signup.html
block_groups_filename = './GeoJSON/' + state + '_block_groups.geojson'
try:
    # if we have it already d/loaded.
    df = gpd.read_file(block_groups_filename)

except IOError:
    # This is what we want from the API:
    request_obj = {
        'level': 'county',
        'sublevel': True,  # I am not sure about this
        'state': state,
        'variables': ['population'],
        'api': 'acs5',  # which census
        'container': 'state',  # what area to get from this state
        'year': 2014  # change to even newer one, 2015, when available
    }
    # request_obj now contains all the counties in state, but we want the block
    # groups, so...

    # Here we load/save the API's response to us asking for all counties in a state:
    state_by_county_filename = './GeoJSON/' + state + '_counties.geojson'

    # This returns a GeoJSON: Geographical JavaScript Object Notation, a dict
    response = requests.post(request_url, auth=HTTPBasicAuth(apikey, None),
                             json=request_obj)
    data = response.json()

    # if we want to save it locally for development and to limit http requests.
    with open(state_by_county_filename, 'w') as outfile:
        json.dump(data, outfile)
    df_state_by_county = gpd.read_file(state_by_county_filename)

    for county_index, county_row in df_state_by_county.iterrows():
        print 'county', int(county_index)
        block_groups_by_county_filename = './GeoJSON/' + state + '_' +\
            'county_' + str(county_index) + '_block_groups.geojson'

        # so now we want to send a request for the block groups per county
        request_obj = {
            'level': 'blockGroup',  # we want the block groups (one level above blocks)
            'sublevel': True,  # I am not sure about this
            'state': state,
            'variables': ['population'],
            'api': 'acs5',  # which census
            'container': 'county',  # what area to get from this state
            'year': 2014,  # change to even newer one, 2015, when available
            'lat': county_row['CENTLAT'],
            'lng': county_row['CENTLON']
        }
        response = requests.post(request_url, auth=HTTPBasicAuth(apikey, None),
                                 json=request_obj)
        data = response.json()

        # save it locally
        with open(block_groups_by_county_filename, 'w') as outfile:
            json.dump(data, outfile)
        # merge the df to get one huge df for the whole state which contains all
        # the group blocks.
        try:
            df = df.append(gpd.read_file(block_groups_by_county_filename),\
                           ignore_index=True)
        except NameError:
            df = gpd.read_file(block_groups_by_county_filename)
        # the block groups by county file is now useless, delete it:
        os.remove(block_groups_by_county_filename)
    # the counties for the whole state file is now useless, delete it:
    os.remove(state_by_county_filename)
    # now that we have finished with all the geoJSON files and marged them into
    # a single dataframe, we save it:
    with open(block_groups_filename, 'w') as outfile:
        # df.to_csv(outfile)
        outfile.write(df.to_json())
################################################################################

# So we did all that, when we could have done (if it worked for all states, only
# works for like RI and some other small states):
request_obj = {
    'level': 'blockGroup',  # we want the block groups (one level above blocks)
    'sublevel': True,  # I am not sure about this
    'state': state,
    'variables': ['population'],
    'api': 'acs5',  # which census
    'container': 'state',  # what area to get from this state
    'year': 2014  # change to even newer one, 2015, when available
}
response = requests.post(request_url, auth=HTTPBasicAuth(apikey, None),
                         json=request_obj)
data = response.json()
# save it locally
whole_state_filename = './GeoJSON/' + state + '.geojson'

with open(whole_state_filename, 'w') as outfile:
    json.dump(data, outfile)
whole_state_df = gpd.read_file(whole_state_filename)

# below we print the rows and columns of the two dataframes
print len(whole_state_df), list(whole_state_df)
print len(df), list(df)
