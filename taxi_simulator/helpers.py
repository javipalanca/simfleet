import json
import logging
import os
import random

import requests
from geopy.distance import vincenty
from requests.adapters import HTTPAdapter
from spade.AID import aid
from urllib3 import Retry

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


def request_path(ori, dest):
    if ori[0] == dest[0] and ori[1] == dest[1]:
        return [[ori[1], ori[0]]], 0, 0
    try:
        url = "http://osrm.gti-ia.upv.es/route/v1/car/{src1},{src2};{dest1},{dest2}?geometries=geojson&overview=full"
        src1, src2, dest1, dest2 = ori[1], ori[0], dest[1], dest[0]
        url = url.format(src1=src1, src2=src2, dest1=dest1, dest2=dest2)

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=1.0)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount(url, adapter)
        result = session.get(url)
        result = json.loads(result.content)

        path = result["routes"][0]["geometry"]["coordinates"]
        path = [[point[1], point[0]] for point in path]
        duration = result["routes"][0]["duration"]
        distance = result["routes"][0]["distance"]
        if path[-1] != dest:
            path.append(dest)
        return path, distance, duration
    except Exception as e:
        logger.error("Error requesting route: {}".format(e))
    return None, None, None


def kmh_to_ms(speed_in_kmh):
    meters_per_second = speed_in_kmh * 1000 / 3600
    return meters_per_second


class PathRequestException(Exception):
    pass


class AlreadyInDestination(Exception):
    pass
