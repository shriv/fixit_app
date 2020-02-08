""" app.py
    Source:
    https://python-visualization.github.io/folium/flask.html

    Required packages:
    - flask
    - folium

    Usage:

    Start the flask server by running:

        $ python flask_example.py

    And then head to http://127.0.0.1:5001/

"""

from flask import Flask
import folium
import pandas as pd
import numpy as np


def get_data():
    fixit_df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vTw6mmYBzkbfIj4bjDHgfg0cebumhMEzrLkC290T0Zpp1t4o7Z8I4ep6MdwnwdvQsEydHaVjmYVmWsp/pub?output=tsv', sep='\t')

    fixit_df['trap_code'] = (fixit_df['Trap Number']
                              .astype(str)
                              .apply(lambda x : x.strip().upper())
                              .apply(lambda x : x.replace('0', 'O'))
                              .apply(lambda x : x.replace('#', '-')) )

    fixit_df['date'] = pd.to_datetime(fixit_df['Date Reported'], errors='coerce')

    loc_df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vRWRILLGLCWk6dVYY7BeF7NH94_tMamKOmOacmzmTjDzfazTZUyegyryS7aLu3c3P0Mp26fGsblMoOE/pub?output=tsv', sep='\t')

    joined_df = pd.merge(fixit_df, loc_df, how = 'left')

    # Remove null locations and keeping active fixit
    data_clean = joined_df[~(joined_df['lat'].isnull() |
                             joined_df['lon'].isnull())]

    return data_clean

def clean_data():
    data_clean = get_data()
    data_clean = data_clean[data_clean['date'] >= '2019-12-01']
    return data_clean

app = Flask(__name__)

@app.route('/')
def index():
    data_clean = clean_data()
    # Pull out relevant columns for leaflet map
    vname = list(data_clean["Trap Number"])
    lat = list(data_clean["lat"])
    lon = list(data_clean["lon"])
    elev = list(data_clean["date"].dt.strftime('%Y-%m-%d'))
    status = list(data_clean["Description From Trapper"])

    map = folium.Map(location=[-41.3, 174.9], zoom_start=12, tiles="OpenStreetMap")

    fgv = folium.FeatureGroup(name="Traps")

    for lt, ln, el, st, vnm in zip(lat, lon, elev, status, vname):
        fgv.add_child(folium.CircleMarker(location=[lt, ln], radius = 8, popup= folium.Popup("<b> Trap: </b>" + vnm + "<br> " +
                "<b> Reported: </b>" + el + "<br> ", max_width=450),
        fill_color='red', color = 'red', fill=True, fill_opacity=0.7))

    map.add_child(fgv)
    map.add_child(folium.LayerControl())
    return map._repr_html_()
#
# def index():
#     start_coords = (-41.3, 174.77)
#     folium_map = folium.Map(location=start_coords, zoom_start=14)
#     return folium_map._repr_html_()


if __name__ == '__main__':
    app.run(debug=True)
