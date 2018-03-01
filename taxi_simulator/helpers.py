import json
import logging
import os
import random

from geopy.distance import vincenty
from spade.AID import aid

logger = logging.getLogger()


def build_aid(agent_id):
    return aid(name=agent_id + "@127.0.0.1", addresses=["xmpp://" + agent_id + "@127.0.0.1"])


coordinator_aid = build_aid("coordinator")


def content_to_json(msg):
    return json.loads(msg.getContent().replace("'", '"'))


def random_position():
    path = os.path.dirname(__file__) + os.sep + "templates" + os.sep + "data" + os.sep + "taxi_stations.json"
    with open(path) as f:
        stations = json.load(f)["features"]
        pos = random.choice(stations)
        coords = [pos["geometry"]["coordinates"][1], pos["geometry"]["coordinates"][0]]
        lat = float("{0:.6f}".format(coords[0]))
        lng = float("{0:.6f}".format(coords[1]))
        return [lat, lng]


def are_close(coord1, coord2, tolerance=10):
    return vincenty(coord1, coord2).meters < tolerance


def distance_in_meters(coord1, coord2):
    return vincenty(coord1, coord2).meters


def kmh_to_ms(speed_in_kmh):
    meters_per_second = speed_in_kmh * 1000 / 3600
    return meters_per_second


class PathRequestException(Exception):
    pass


class AlreadyInDestination(Exception):
    pass
