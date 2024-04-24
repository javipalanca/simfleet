import asyncio
import json
import time

from loguru import logger

from spade.message import Message

from simfleet.utils.helpers import (
    #random_position,
    distance_in_meters,
    kmh_to_ms,
    PathRequestException,
    AlreadyInDestination,
)

MIN_AUTONOMY = 2

class ChargeableMixin:

    def __init__(self):

        self.current_autonomy_km = 2000         #transport.py
        self.max_autonomy_km = 2000             #transport.py

        #statics
        self.total_charging_time = 0.0

    # transport.py
    def set_autonomy(self, autonomy, current_autonomy=None):
        self.max_autonomy_km = autonomy
        self.current_autonomy_km = (
            current_autonomy if current_autonomy is not None else autonomy
        )

    # transport.py
    def get_autonomy(self):
        return self.current_autonomy_km

    # transport.py - Decremanta autonomia
    def set_km_expense(self, expense=0):
        self.current_autonomy_km -= expense

    # transport.py - Incrementa autonomia
    def transport_charged(self):
        self.current_autonomy_km = self.max_autonomy_km
        self.total_charging_time += time.time() - self.charge_time

    # transport.py
    def calculate_km_expense(self, current_pos, origin, dest=None):
        fir_distance = distance_in_meters(current_pos, origin)
        sec_distance = distance_in_meters(origin, dest)
        if dest is None:
            sec_distance = 0
        return (fir_distance + sec_distance) // 1000

    # electrictaxi.py
    def has_enough_autonomy(self, customer_orig, customer_dest):
        autonomy = self.get_autonomy()
        if autonomy <= MIN_AUTONOMY:
            logger.warning(
                "{} has not enough autonomy ({}).".format(self.name, autonomy)
            )
            return False
        travel_km = self.calculate_km_expense(
            #self.get("current_pos"), customer_orig, customer_dest
            self.get_position(), customer_orig, customer_dest
        )
        logger.debug(
            "Transport {} has autonomy {} when max autonomy is {}"
            " and needs {} for the trip".format(
                self.name,
                self.get_autonomy(),
                self.max_autonomy_km,
                travel_km,
            )
        )

        if autonomy - travel_km < MIN_AUTONOMY:
            logger.warning(
                "{} has not enough autonomy to do travel ({} for {} km).".format(
                    self.name, autonomy, travel_km
                )
            )
            return False
        return True

    # electrictaxi.py
    def check_and_decrease_autonomy(self, customer_orig, customer_dest):
        autonomy = self.get_autonomy()
        travel_km = self.calculate_km_expense(
            #self.get("current_pos"), customer_orig, customer_dest
            self.get_position(), customer_orig, customer_dest
        )
        if autonomy - travel_km < MIN_AUTONOMY:
            logger.warning(
                "{} has not enough autonomy to do travel ({} for {} km).".format(
                    self.agent.name, autonomy, travel_km
                )
            )
            return False
        self.set_km_expense(travel_km)
        return True


