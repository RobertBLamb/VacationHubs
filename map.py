import numpy as np
import pandas as pd

import folium
import geopy
from geopy import distance

from sklearn.neighbors._nearest_centroid import NearestCentroid
from scipy.cluster.hierarchy import linkage, fcluster, fclusterdata, dendrogram
import googlemaps
import matplotlib.pyplot as plt


import os

API_KEY = os.environ.get('GOOGLE_MAP_KEY')
gmaps = googlemaps.Client(key=API_KEY)
locations_to_map = []
map_ = folium.Map
point_size = 15


class Points:

    all_points = set()

    def __init__(self, address, geo, name):
        self.name = name
        self.address = address
        self.geo = geo


def clear_set():
    Points.all_points = set()


def new_point(address_to_search):
    global map_
    address, geo, name = get_location_info(address_to_search)
    folium.CircleMarker(location=[geo['lat'], geo['lng']], popup=name,
                        color='black', fill=True,
                        radius=15).add_to(map_)


def get_location_info(address_to_search):
    p_id = gmaps.find_place(input=address_to_search, input_type='textquery')['candidates'][0]['place_id']
    place = gmaps.place(place_id=p_id)['result']

    address = place['formatted_address']
    geometry = place['geometry']['location']
    name = place['name']
    Points.all_points.add(Points(address, geometry, name))
    return address, geometry, name


# todo: decide on better way to have a starting point
def new_map():
    global map_
    city = "Kyoto"
    # get location
    locator = geopy.geocoders.Nominatim(user_agent="MyCoder")
    location = locator.geocode(city)
    print(location)
    # keep latitude and longitude only
    location = [location.latitude, location.longitude]
    print("[lat, lon]:", location)
    # todo: this stays
    map_ = folium.Map(location=location, tiles="cartodbpositron",
               zoom_start=11)


def make_map():
    # todo: temporary until user is able to give input
    # region temp values
    point_array = []
    for point in Points.all_points:
        point_array.append([point.name, float(point.geo['lat']), float(point.geo['lng'])])

    point_array = np.array(point_array)
    dtf = pd.DataFrame(point_array)
    dtf[3] = 15
    dtf.head()


    # region where to start map
    city = "Kyoto"
    # get location
    locator = geopy.geocoders.Nominatim(user_agent="MyCoder")
    location = locator.geocode(city)
    print(location)
    # keep latitude and longitude only
    location = [location.latitude, location.longitude]
    print("[lat, lon]:", location)
    # endregion
    # 0 = name, 1 = lat, 2 = lng, 3 = size, 4 = cluster
    centroids = get_centroids(dtf)
    cluster_points(dtf, location, centroids)


def get_centroids(dtf):
    X = dtf[[1, 2]]
    # generate the linkage matrix
    cluster = fcluster(linkage(X), .10, criterion='distance')
    dtf[[4]] = cluster

    # centroid information
    y = np.array(cluster)
    clf = NearestCentroid()
    # todo: error if only one cluster
    clf.fit(X, y)
    cluster_centers = clf.centroids_
    return cluster_centers


def cluster_points(dtf, location, cluster_centers):
    # region cluster map
    x, y = 1, 2
    color = 4
    size = 3
    popup = 0
    data = dtf.copy()

    # create color column
    lst_elements = sorted(list(dtf[color].unique()))
    lst_colors = ['#%06X' % np.random.randint(0, 0xFFFFFF) for i in
                  range(len(lst_elements))]
    data[color] = data[color].apply(lambda x:
                                      lst_colors[lst_elements.index(x)])

    # initialize the map with the starting location
    global map_
    map_ = folium.Map(location=location, tiles="cartodbpositron",
                      zoom_start=11)

    # add points
    data.apply(lambda row: folium.CircleMarker(
        location=[row[x], row[y]], popup=row[popup],
        color=row[color], fill=True,
        radius=row[size]).add_to(map_), axis=1)

    # region legend
    # add html legend
    legend_html = """<div style="position:fixed; bottom:10px; left:10px; border:2px solid black; z-index:9999; font-size:14px;">&nbsp;<b>""" + "Hubs" + """:</b><br>"""
    for i in lst_elements:
        legend_html = legend_html + """&nbsp;<i class="fa fa-circle
         fa-1x" style="color:""" + lst_colors[lst_elements.index(i)] + """">
         </i>&nbsp;""" + str(i) + """<br>"""
    legend_html = legend_html + """</div>"""
    map_.get_root().html.add_child(folium.Element(legend_html))
    # endregion

    # todo: turn back on when project is done
    # add centroids marker
    for points in cluster_centers:
        arr = list(points)

        hotel = ''

        recommended_site = gmaps.places_nearby(location=arr, radius=500, type='lodging')
        try:
            hotel = str(recommended_site['results'][0]['name'])
        except:
            hotel = 'There are no hotels closeby this location'
        folium.Marker(location=[points[0], points[1]],
                      popup=hotel, draggable=False,
                      icon=folium.Icon(color="black")).add_to(map_)

    # plot the map
    # endregion



