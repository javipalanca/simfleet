import json
import random
import socket

import requests
from spade.AID import aid

REGISTER_PROTOCOL = "REGISTER"
CREATE_PROTOCOL = "CREATE"

TAXI_WAITING = 10
TAXI_MOVING_TO_PASSENGER = 11
TAXI_MOVING_TO_DESTINY = 12

PASSENGER_WAITING = 20
PASSENGER_IN_TAXI = 21
PASSENGER_IN_DEST = 22

simulator_aid = aid(name="coordinator@127.0.0.1", addresses=["xmpp://coordinator@127.0.0.1"])


def random_position():
    with open("taxi_simulator/templates/data/taxi_stations.json") as f:
        stations = json.load(f)["features"]
        pos = random.choice(stations)
        return [pos["geometry"]["coordinates"][1], pos["geometry"]["coordinates"][0]]


def unused_port(hostname):
    """Return a port that is unused on the current host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((hostname, 0))
    port = s.getsockname()[1]
    s.close()
    return port


def request_path(ori, dest):
    url = "http://router.project-osrm.org/route/v1/car/{src1},{src2};{dest1},{dest2}?geometries=geojson&overview=full"
    src1, src2, dest1, dest2 = ori[1], ori[0], dest[1], dest[0]
    url = url.format(src1=src1, src2=src2, dest1=dest1, dest2=dest2)
    result = requests.get(url)
    result = json.loads(result.content)
    path = result["routes"][0]["geometry"]["coordinates"]
    path = [[point[1], point[0]] for point in path]
    duration = result["routes"][0]["duration"]
    distance = result["routes"][0]["distance"]

    return path, distance, duration
