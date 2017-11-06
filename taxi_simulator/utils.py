import json
import random

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
