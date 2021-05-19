import numpy as np
import pandas as pd

import folium
import geopy

from sklearn.neighbors._nearest_centroid import NearestCentroid
from scipy.cluster.hierarchy import linkage, fcluster
import googlemaps

import os

API_KEY = os.environ.get('GOOGLE_MAP_KEY')
gmaps = googlemaps.Client(key=API_KEY)
locations_to_map = []
map_ = folium.Map
point_size = 15


class Points:

    all_points = set()
    starting_loc = []

    def __init__(self, address, geo, name):
        self.name = name
        self.address = address
        self.geo = geo


def clear_set():
    Points.all_points = set()
    Points.starting_loc = []


def new_point(address_to_search):
    global map_
    address, geo, name = get_location_info(address_to_search)
    if len(Points.all_points) == 1:

        Points.starting_loc = [geo['lat'], geo['lng']]
        map_ = folium.Map(location=Points.starting_loc, height='77.5%', tiles="cartodbpositron", zoom_start=11)

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


def new_map():
    global map_
    city = "Kyoto"
    # get location
    locator = geopy.geocoders.Nominatim(user_agent="MyCoder")
    location = locator.geocode(city)
    # keep latitude and longitude only
    location = [location.latitude, location.longitude]
    # todo: this stays
    map_ = folium.Map(location=location, height='77.5%', tiles="cartodbpositron", zoom_start=11)


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

    # 0 = name, 1 = lat, 2 = lng, 3 = size, 4 = cluster
    centroids = get_centroids(dtf)
    cluster_points(dtf, Points.starting_loc, centroids)


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
    # region setup data for interpretation
    x, y = 1, 2
    color = 4
    size = 3
    popup = 0
    data = dtf.copy()
    # endregion

    # region give each cluster value a color
    lst_elements = sorted(list(dtf[color].unique()))
    lst_colors = ['#%06X' % np.random.randint(0, 0xFFFFFF) for _ in
                  range(len(lst_elements))]
    data[color] = data[color].apply(lambda x:
                                      lst_colors[lst_elements.index(x)])
    # endregion

    # region starting point for map
    global map_
    map_ = folium.Map(location=location, height='77.5%', tiles="cartodbpositron",
                      zoom_start=11)
    # endregion

    # region add points to map
    data.apply(lambda row: folium.CircleMarker(
        location=[row[x], row[y]], popup=row[popup],
        color=row[color], fill=True,
        radius=row[size]).add_to(map_), axis=1)
    # endregion

    # region legend
    legend_html = """<div style="position:fixed; bottom:10px; left:10px; border:2px solid black; z-index:9999; font-size:14px;">&nbsp;<b>""" + "Hubs" + """:</b><br>"""
    for i in lst_elements:
        legend_html = legend_html + """&nbsp;<i class="fa fa-circle
         fa-1x" style="color:""" + lst_colors[lst_elements.index(i)] + """">
         </i>&nbsp;""" + str(i) + """<br>"""
    legend_html = legend_html + """</div>"""
    map_.get_root().html.add_child(folium.Element(legend_html))
    # endregion

    # region add centroids / hotel recommendations
    for points in cluster_centers:
        arr = list(points)

        recommended_site = gmaps.places_nearby(location=arr, radius=500, type='lodging')
        try:
            hotel = str(recommended_site['results'][0]['name'])
        except Exception as e:
            hotel = 'There are no hotels closeby this location'
            print(e)
        folium.Marker(location=[points[0], points[1]],
                      popup=hotel, draggable=False,
                      icon=folium.Icon(color="black")).add_to(map_)
    # endregion

