import json
import random
import socket

from spade.AID import aid

REGISTER_PROTOCOL = "REGISTER"
CREATE_PROTOCOL = "CREATE"

TAXI_WAITING = 0
TAXI_MOVING_TO_PASSENGER = 1
TAXI_MOVING_TO_DESTINY = 2

simulator_aid = aid(name="simulator@127.0.0.1", addresses=["xmpp://simulator@127.0.0.1"])


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
