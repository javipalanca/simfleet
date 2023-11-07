import asyncio
import json
import os
import socket
import sys
import time
import uuid
from abc import ABCMeta
from importlib import import_module

import aiohttp
from loguru import logger
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template

from .helpers import distance_in_meters, kmh_to_ms

TRANSPORT_WAITING = "TRANSPORT_WAITING"
TRANSPORT_MOVING_TO_CUSTOMER = "TRANSPORT_MOVING_TO_CUSTOMER"
TRANSPORT_IN_CUSTOMER_PLACE = "TRANSPORT_IN_CUSTOMER_PLACE"
TRANSPORT_MOVING_TO_DESTINATION = "TRANSPORT_MOVING_TO_DESTINATION"
TRANSPORT_WAITING_FOR_APPROVAL = "TRANSPORT_WAITING_FOR_APPROVAL"

TRANSPORT_MOVING_TO_STATION = "TRANSPORT_MOVING_TO_STATION"
TRANSPORT_IN_STATION_PLACE = "TRANSPORT_IN_STATION_PLACE"
TRANSPORT_WAITING_FOR_STATION_APPROVAL = "TRANSPORT_WAITING_FOR_STATION_APPROVAL"
TRANSPORT_NEEDS_CHARGING = "TRANSPORT_NEEDS_CHARGING"
TRANSPORT_CHARGING = "TRANSPORT_LOADING"
TRANSPORT_CHARGED = "TRANSPORT_LOADED"

FREE_STATION = "FREE_STATION"
BUSY_STATION = "BUSY_STATION"

CUSTOMER_WAITING = "CUSTOMER_WAITING"
CUSTOMER_IN_TRANSPORT = "CUSTOMER_IN_TRANSPORT"
CUSTOMER_IN_DEST = "CUSTOMER_IN_DEST"
CUSTOMER_LOCATION = "CUSTOMER_LOCATION"
CUSTOMER_ASSIGNED = "CUSTOMER_ASSIGNED"


def status_to_str(status_code):
    """
    Translates an int status code to a string that represents the status

    Args:
        status_code (int): the code of the status

    Returns:
        str: the string that represents the status
    """
    statuses = {
        10: "TRANSPORT_WAITING",
        11: "TRANSPORT_MOVING_TO_CUSTOMER",
        12: "TRANSPORT_IN_CUSTOMER_PLACE",
        13: "TRANSPORT_MOVING_TO_DESTINATION",
        14: "TRANSPORT_WAITING_FOR_APPROVAL",
        15: "TRANSPORT_MOVING_TO_STATION",
        16: "TRANSPORT_IN_STATION_PLACE",
        17: "TRANSPORT_WAITING_FOR_STATION_APPROVAL",
        18: "TRANSPORT_LOADING",
        19: "TRANSPORT_LOADED",
        20: "CUSTOMER_WAITING",
        21: "CUSTOMER_IN_TRANSPORT",
        22: "CUSTOMER_IN_DESTINATION",
        23: "CUSTOMER_LOCATION",
        24: "CUSTOMER_ASSIGNED",
        30: "FREE_STATION",
        31: "BUSY_STATION",
    }
    if status_code in statuses:
        return statuses[status_code]
    return status_code


class StrategyBehaviour(CyclicBehaviour, metaclass=ABCMeta):
    """
    The behaviour that all parent strategies must inherit from. It complies with the Strategy Pattern.
    """

    pass


class RequestRouteBehaviour(OneShotBehaviour):
    """
    A one-shot behaviour that is executed to request for a new route to the route agent.
    """

    def __init__(self, msg: Message, origin: list, destination: list, route_host: str):
        """
        Behaviour to request a route to a route agent
        Args:
            msg (Message): the message to be sent
            origin (list): origin of the route
            destination (list): destination of the route
            route_host (str): name of the route host server
        """
        self.origin = origin
        self.destination = destination
        self._msg = msg
        self.route_host = route_host
        self.result = {"path": None, "distance": None, "duration": None}
        super().__init__()

    async def run(self):
        try:
            response_time = time.time()
            path, distance, duration = await request_route_to_server(
                self.origin, self.destination, self.route_host
            )
            response_time = time.time() - response_time
            if path is None:
                logger.error(
                    "There was an unknown error requesting the route. Response time={}".format(
                        response_time
                    )
                )
                self.exit_code = {"type": "error"}
                self.kill()
                return
            logger.debug("Got route in response time={}".format(response_time))
            reply_content = {
                "path": path,
                "distance": distance,
                "duration": duration,
                "type": "success",
            }
            self.kill(json.loads(json.dumps(reply_content)))

        except Exception as e:
            response_time = time.time() - response_time
            logger.error(
                "Exception requesting route, response time={}, error: {} ".format(
                    response_time, e
                )
            )


async def request_path(agent, origin, destination, route_host):
    """
    Sends a message to the RouteAgent to request a path

    Args:
        agent: the agent who is requesting the path
        origin (list): a list with the origin coordinates [longitude, latitude]
        destination (list): a list with the target coordinates [longitude, latitude]
        route_host (str): name of the route host server

    Returns:
        list, float, float: a list of points (longitude and latitude) representing the path,
                            the distance of the path in meters, a estimation of the duration of the path

    Examples:
        >>> path, distance, duration = request_path(agent, origin=[0,0], destination=[1,1])
        >>> print(path)
        [[0,0], [0,1], [1,1]]
        >>> print(distance)
        2.0
        >>> print(duration)
        3.24
    """
    if origin[0] == destination[0] and origin[1] == destination[1]:
        return [[origin[1], origin[0]]], 0, 0

    msg = Message()
    msg.thread = str(uuid.uuid4()).replace("-", "")
    template = Template()
    template.thread = msg.thread
    behav = RequestRouteBehaviour(msg, origin, destination, route_host)
    agent.add_behaviour(behav, template)

    while not behav.is_killed():
        await asyncio.sleep(0.01)

    if (
        behav.exit_code is {}
        or "type" in behav.exit_code
        and behav.exit_code["type"] == "error"
    ):
        return None, None, None
    else:
        return (
            behav.exit_code["path"],
            behav.exit_code["distance"],
            behav.exit_code["duration"],
        )


def unused_port(hostname):
    """Return a port that is unused on the current host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((hostname, 0))
    port = s.getsockname()[1]
    s.close()
    return port


def chunk_path(path, speed_in_kmh):
    """
    Splits the path into smaller chunks taking into account the speed.

    Args:
        path (list): the original path. A list of points (lon, lat)
        speed_in_kmh (float): the speed in km per hour at which the path is being traveled.

    Returns:
        list: a new path equivalent (to the first one), that has at least the same number of points.
    """
    meters_per_second = kmh_to_ms(speed_in_kmh)
    length = len(path)
    chunked_lat_lngs = []

    for i in range(1, length):
        _cur = path[i - 1]
        _next = path[i]
        if _cur == _next:
            continue
        distance = distance_in_meters(_cur, _next)
        factor = meters_per_second / distance if distance else 0
        diff_lat = factor * (_next[0] - _cur[0])
        diff_lng = factor * (_next[1] - _cur[1])

        if distance > meters_per_second:
            while distance > meters_per_second:
                _cur = [_cur[0] + diff_lat, _cur[1] + diff_lng]
                distance = distance_in_meters(_cur, _next)
                chunked_lat_lngs.append(_cur)
        else:
            chunked_lat_lngs.append(_cur)

    chunked_lat_lngs.append(path[length - 1])

    return chunked_lat_lngs


def load_class(class_path):
    """
    Tricky method that imports a class form a string.

    Args:
        class_path (str): the path where the class to be imported is.

    Returns:
        class: the class imported and ready to be instantiated.
    """
    sys.path.append(os.getcwd())
    module_path, class_name = class_path.rsplit(".", 1)
    mod = import_module(module_path)
    return getattr(mod, class_name)


def avg(array):
    """
    Makes the average of an array without Nones.
    Args:
        array (list): a list of floats and Nones

    Returns:
        float: the average of the list without the Nones.
    """
    array_wo_nones = list(filter(None, array))
    return (
        (sum(array_wo_nones, 0.0) / len(array_wo_nones))
        if len(array_wo_nones) > 0
        else 0.0
    )


async def request_route_to_server(
    origin, destination, route_host="http://router.project-osrm.org/"
):
    """
    Queries the OSRM for a path.

    Args:
        origin (list): origin coordinate (longitude, latitude)
        destination (list): target coordinate (longitude, latitude)
        route_host (string): route to host server of OSRM service

    Returns:
        list, float, float = the path, the distance of the path and the estimated duration
    """
    try:

        url = (
            route_host
            + "route/v1/car/{src1},{src2};{dest1},{dest2}?geometries=geojson&overview=full"
        )
        src1, src2, dest1, dest2 = origin[1], origin[0], destination[1], destination[0]
        url = url.format(src1=src1, src2=src2, dest1=dest1, dest2=dest2)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                result = await response.json()

        path = result["routes"][0]["geometry"]["coordinates"]
        path = [[point[1], point[0]] for point in path]
        duration = result["routes"][0]["duration"]
        distance = result["routes"][0]["distance"]
        if path[-1] != destination:
            path.append(destination)
        return path, distance, duration
    except Exception as e:
        return None, None, None
