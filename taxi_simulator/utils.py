import os
import sys
import time
import logging
import socket
from importlib import import_module
from abc import ABCMeta

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

from spade.Behaviour import Behaviour

from helpers import distance_in_meters, kmh_to_ms

logger = logging.getLogger()

TAXI_WAITING = 10
TAXI_MOVING_TO_PASSENGER = 11
TAXI_IN_PASSENGER_PLACE = 12
TAXI_MOVING_TO_DESTINY = 13
TAXI_WAITING_FOR_APPROVAL = 14

PASSENGER_WAITING = 20
PASSENGER_IN_TAXI = 21
PASSENGER_IN_DEST = 22
PASSENGER_LOCATION = 23
PASSENGER_ASSIGNED = 24


class StrategyBehaviour(Behaviour):
    __metaclass__ = ABCMeta

    def store_value(self, key, value):
        self.myAgent.store_value(key, value)

    def get_value(self, key):
        return self.myAgent.get_value(key)

    def has_value(self, key):
        return self.myAgent.has_value(key)

    def timeout_receive(self, timeout=5):
        """
        Waits for a message until timeout is done.
        If a message is received the method returns immediately.
        If the time has passed and no message has been received, it returns None.
        :param timeout: number of seconds to wait for a message
        :type timeout: :class:`int`
        :return: a message or None
        :rtype: :class:`ACLMessage` or None
        """
        init_time = time.time()
        while (time.time() - init_time) < timeout:
            msg = self._receive(block=False)
            if msg is not None:
                return msg
            time.sleep(0.1)
        return None


def unused_port(hostname):
    """Return a port that is unused on the current host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((hostname, 0))
    port = s.getsockname()[1]
    s.close()
    return port


def chunk_path(path, speed_in_kmh):
    meters_per_second = kmh_to_ms(speed_in_kmh)
    length = len(path)
    chunked_lat_lngs = []

    for i in range(1, length):
        _cur = path[i - 1]
        _next = path[i]
        distance = distance_in_meters(_cur, _next)
        factor = meters_per_second / distance
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
    sys.path.append(os.getcwd())
    module_path, class_name = class_path.rsplit(".", 1)
    mod = import_module(module_path)
    return getattr(mod, class_name)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator
