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
from scipy.interpolate import splrep, splev, UnivariateSpline

def get_data():
    fixit_df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vSwfyvQHwOopLW2pPDLm3wMZnaNTBlAleWZMeSf3uZVNUtJFoclY1ocYMk_6ywJts_OfiZHG71ShmsJ/pub?output=tsv', sep='\t')

    fixit_df['trap_code'] = (fixit_df['Trap Number']
                              .astype(str)
                              .apply(lambda x : x.strip().upper())
                              .apply(lambda x : x.replace('0', 'o'))
                              .apply(lambda x : x.replace('#', '-')) )

    fixit_df['date'] = pd.to_datetime(fixit_df['Date Reported'], errors='coerce')
    
    loc_df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vRWRILLGLCWk6dVYY7BeF7NH94_tMamKOmOacmzmTjDzfazTZUyegyryS7aLu3c3P0Mp26fGsblMoOE/pub?output=tsv', sep='\t')

    return fixit_df, loc_df

def return_fixit_with_loc(fixit_df, loc_df):
    joined_df = pd.merge(fixit_df, loc_df, how = 'left')

    # remove null locations and keeping active fixit
    data_clean = joined_df[~(joined_df['lat'].isnull() |
                             joined_df['lon'].isnull())]

    return data_clean


############################
## main app functionality ##
############################

app = Flask(__name__)

@app.route('/')
def index():
    # get data from google sheets
    fixit_df, loc_df = get_data()
    data_clean = return_fixit_with_loc(fixit_df, loc_df)
    fixit_to_do = data_clean[data_clean['Date Trap Fixed'].isnull()]

    # pull out relevant columns for leaflet map
    vname = list(fixit_to_do["Trap Number"])
    lat = list(fixit_to_do["lat"])
    lon = list(fixit_to_do["lon"])
    elev = list(fixit_to_do["date"].dt.strftime('%Y-%m-%d'))
    issue = list(fixit_to_do["Description From Trapper"])

    # make map
    map = folium.Map(location=[-41.3, 174.9], zoom_start=12, tiles="OpenStreetMap")

    # traps layer
    fgv = folium.FeatureGroup(name="Fixit To Do")

    # add points
    for lt, ln, el, iss, vnm in zip(lat, lon, elev, issue, vname):
        fgv.add_child(folium.CircleMarker(location=[lt, ln],
                                          radius = 8,
                                          popup = folium.Popup("<b> Trap: </b>" +
                                                               vnm + "<br> " +
                                                               "<b> Reported: </b>" +
                                                               el + "<br> " +
                                                               "<b> Issue: </b>" +
                                                               iss + "<br> ",
                                                               max_width=450),
                                          fill_color='red',
                                          color = 'red',
                                          fill=True,
                                          fill_opacity=0.7))
    map.add_child(fgv)    


    # traplines layer
    tpln = folium.FeatureGroup(name="trap lines")

    # add lines by trapline
    loc_df['trapline_letter_code'] = (loc_df['trap_code']
                                      .str
                                      .extract(r'([A-Z]+)', expand=False))
    loc_df['trapline_number'] = (loc_df['trap_code']
                                 .str
                                 .extract(r'(\d+)', expand=False))
    # data_clean = loc_df[loc_df['trapline_letter_code'].isin(['bv', 'bo', 'et', 'rt'])]

    for group in unique(loc_df['trapline_letter_code']):
        data_subset = (loc_df[loc_df['trapline_letter_code'] == group]
                       .sort_values(['lon', 'lat'], axis=0))

        # Smooth trap line tracks
        new_lon = np.linspace(min(data_subset['lon']), max(data_subset['lon']), 50)
        # new_lat = np.linspace(min(data_subset['lat']), max(data_subset['lat']), 50)
        if len(data_subset['lat']) > 10:
            print(group)
            # spline_lon = UnivariateSpline(range(len(data_subset['lon'])), data_subset['lon'], k = 2)
            # spline_lat = UnivariateSpline(range(len(data_subset['lat'])), data_subset['lat'], k = 2)
            spline_both = UnivariateSpline(data_subset['lon'], data_subset['lat'], k = 2)
            fit_lat = spline_both(new_lon)
            tracks = list(zip(fit_lat, new_lon))
            tpln.add_child(folium.PolyLine(tracks,
                                           popup = folium.Popup("<b> trapline: </b>" + group)))
        else:
            tracks = list(zip(data_subset['lat'], data_subset['lon']))
            tpln.add_child(folium.PolyLine(tracks,
                                           popup = folium.Popup("<b> Trapline: </b>" + group)))

    map.add_child(tpln)
    map.add_child(folium.LayerControl())


    return map._repr_html_()



if __name__ == '__main__':
    app.run(debug=True)
