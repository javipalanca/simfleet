"""
Helpers module

These functions are useful for the develop of new strategies.
"""

import json
import os
import random
import requests

from geopy.distance import vincenty
from geopy.geocoders import Nominatim

def get_bbox_from_location(location_str, zoom):
    """
    Get BoundingBox from str location

    Return:
        Tupla: (central_point, bbox)
    """
    # Obtener las coordenadas de la ubicación (ciudad, calle, avenida, etc.)
    geolocator = Nominatim(user_agent="zoom_bbox_simfleet")
    location = geolocator.geocode(location_str, addressdetails=True, timeout=10)

    if location is None:
        raise Exception ("Could not find coordinates for the entered location")
        return None

    lat, lon = location.latitude, location.longitude

    # Calcular el Bounding Box en función del zoom
    bbox_width = 360 / (2 ** zoom)
    bbox_height = bbox_width / 2  # Proporción arbitraria para ajustar el Bounding Box

    min_lon = lon - bbox_width / 2
    max_lon = lon + bbox_width / 2
    min_lat = lat - bbox_height / 2
    max_lat = lat + bbox_height / 2

    bbox = (min_lat, min_lon, max_lat, max_lon)
    central_point = [lat, lon]

    return (central_point, bbox)


def random_position():
    """
    Returns a random position inside the map.

    Returns:
        list: a point (longitude and latitude)
    """
    base_dir_utils = os.path.dirname(__file__)
    base_dir = os.path.dirname(base_dir_utils)

    path = (
        base_dir
        + os.sep
        + "templates"
        + os.sep
        + "data"
        + os.sep
        + "taxi_stations.json"
    )
    with open(path) as f:
        stations = json.load(f)["features"]
        pos = random.choice(stations)
        coords = [pos["geometry"]["coordinates"][1], pos["geometry"]["coordinates"][0]]
        lat = float("{0:.6f}".format(coords[0]))
        lng = float("{0:.6f}".format(coords[1]))
        return [lat, lng]


def new_random_position(bbox, route_host):
    """
        Returns a random position inside the map.

        Returns:
            list: a point (longitude and latitude)
    """

    min_lat, min_lon, max_lat, max_lon = bbox

    # Generar ubicación aleatoria dentro del Bounding Box -- Vrs 1
    #random_lon = random.uniform(min_lon, max_lon)
    #random_lat = random.uniform(min_lat, max_lat)

    # Generar ubicación aleatoria dentro del Bounding Box -- Vrs 2
    zoom = random.uniform(1, 3)     # Rango 1 (Sin zoom) - 5 (Zoom en el centro del bbox)
    zoom_factor = 1 / zoom
    random_lon = random.uniform(min_lon + (max_lon - min_lon) * (1 - zoom_factor) / 2, max_lon - (max_lon - min_lon) * (1 - zoom_factor) / 2)
    random_lat = random.uniform(min_lat + (max_lat - min_lat) * (1 - zoom_factor) / 2, max_lat - (max_lat - min_lat) * (1 - zoom_factor) / 2)

    # URL del servicio OSRM
    osrm_url = f'{route_host}/nearest/v1/driving/{random_lon},{random_lat}'

    # Realizar la solicitud a la API de OSRM
    response = requests.get(osrm_url)

    # Comprobar si la solicitud fue exitosa
    if response.status_code == 200:
        result = response.json()
        nearest_coordinates = result['waypoints'][0]['location']
        return [nearest_coordinates[1], nearest_coordinates[0]]
    else:
        raise Exception("OSRM request error")
        return None




def are_close(coord1, coord2, tolerance=10):
    """
    Checks wheter two points are close or not. The tolerance is expressed in meters.

    Args:
        coord1 (list): a coordinate (longitude, latitude)
        coord2 (list): another coordinate (longitude, latitude)
        tolerance (int): tolerance in meters

    Returns:
        bool: whether the two coordinates are closer than tolerance or not
    """
    return vincenty(coord1, coord2).meters < tolerance


def distance_in_meters(coord1, coord2):
    """
    Returns the distance between two coordinates in meters.

    Args:
        coord1 (list): a coordinate (longitude, latitude)
        coord2: another coordinate (longitude, latitude)

    Returns:
        float: distance meters between the two coordinates
    """
    return vincenty(coord1, coord2).meters


def kmh_to_ms(speed_in_kmh):
    """
    Convert kilometers/hour to meters/second.

    Args:
        speed_in_kmh (float): speed in kilometers/hour

    Returns:
        float: the speed in meters/second
    """
    meters_per_second = speed_in_kmh * 1000 / 3600
    return meters_per_second


class PathRequestException(Exception):
    """
    This exception is raised when a path could not be computed.
    """

    pass


class AlreadyInDestination(Exception):
    """
    This exception is raised when an agent wants to move to a destination where it is already there.
    """

    pass

