"""
Helpers module

These functions are useful for the develop of new strategies.
"""

import json
import os
import random

from geopy.distance import vincenty


def random_position():
    """
    Returns a random position inside the map.

    Returns:
        list: a point (longitude and latitude)
    """
    path = os.path.dirname(__file__) + os.sep + "templates" + os.sep + "data" + os.sep + "taxi_stations.json"
    with open(path) as f:
        stations = json.load(f)["features"]
        pos = random.choice(stations)
        coords = [pos["geometry"]["coordinates"][1], pos["geometry"]["coordinates"][0]]
        lat = float("{0:.6f}".format(coords[0]))
        lng = float("{0:.6f}".format(coords[1]))
        return [lat, lng]


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
