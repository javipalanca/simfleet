import time

from loguru import logger

from simfleet.utils.helpers import (
    distance_in_meters,
)

MIN_AUTONOMY = 2

class ChargeableMixin:
    """
        Mixin class that adds charging and autonomy management capabilities to a transport agent.
        It provides methods to manage the autonomy (range) of a vehicle, calculate travel expenses,
        and recharge the vehicle when necessary.

        Attributes:
            current_autonomy_km (int): The current autonomy of the vehicle in kilometers.
            max_autonomy_km (int): The maximum autonomy of the vehicle in kilometers.
            service_type (str): The type of service the vehicle provides (e.g., taxi, delivery).
            total_charging_time (float): The cumulative charging time of the vehicle.
        """

    def __init__(self):
        """
                Initializes the mixin with default values for autonomy and charging time.
        """

        self.current_autonomy_km = 2000         #transport.py
        self.max_autonomy_km = 2000             #transport.py
        self.service_type = None  # New

        #statics
        self.total_charging_time = 0.0

    def set_service_type(self, service_type):
        """
                Sets the type of service the transport provides.

                Args:
                    service_type (str): The type of service (e.g., taxi, delivery).
        """
        self.service_type = service_type

    def set_autonomy(self, autonomy, current_autonomy=None):
        """
                Sets the maximum and current autonomy of the transport.

                Args:
                    autonomy (int): The maximum autonomy in kilometers.
                    current_autonomy (int, optional): The current autonomy. If not provided, it defaults to the maximum autonomy.
                """
        self.max_autonomy_km = autonomy
        self.current_autonomy_km = (
            current_autonomy if current_autonomy is not None else autonomy
        )

    def get_autonomy(self):
        """
                Retrieves the current autonomy of the vehicle.

                Returns:
                    int: The current autonomy in kilometers.
                """
        return self.current_autonomy_km

    def set_km_expense(self, expense=0):
        """
                Reduces the current autonomy based on the travel expense.

                Args:
                    expense (int): The distance in kilometers to subtract from the current autonomy.
                """
        self.current_autonomy_km -= expense

    def transport_charged(self):
        """
                Fully recharges the transport vehicle, restoring its autonomy to the maximum value.
                Also updates the total charging time.
        """
        self.current_autonomy_km = self.max_autonomy_km
        self.total_charging_time += time.time() - self.charge_time

    def calculate_km_expense(self, current_pos, origin, dest=None):
        """
                Calculates the travel distance (in kilometers) from the current position to the customer's location,
                and optionally to the final destination.

                Args:
                    current_pos (list): The current coordinates (x, y) of the transport.
                    origin (list): The origin coordinates (x, y) of the customer.
                    dest (list, optional): The destination coordinates (x, y). Defaults to None.

                Returns:
                    int: The total travel distance in kilometers.
        """
        fir_distance = distance_in_meters(current_pos, origin)
        sec_distance = distance_in_meters(origin, dest)
        if dest is None:
            sec_distance = 0
        return (fir_distance + sec_distance) // 1000

    def has_enough_autonomy(self, customer_orig, customer_dest):
        """
                Checks if the transport has enough autonomy to complete a trip from the customer's origin to the destination.

                Args:
                    customer_orig (list): The coordinates of the customer's origin (x, y).
                    customer_dest (list): The coordinates of the customer's destination (x, y).

                Returns:
                    bool: True if the transport has enough autonomy, False otherwise.
                """
        autonomy = self.get_autonomy()
        if autonomy <= MIN_AUTONOMY:
            logger.warning(
                "{} has not enough autonomy ({}).".format(self.name, autonomy)
            )
            return False
        travel_km = self.calculate_km_expense(
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

    def check_and_decrease_autonomy(self, customer_orig, customer_dest):
        """
                Verifies if the transport has enough autonomy for a trip and decreases the autonomy if possible.

                Args:
                    customer_orig (list): The coordinates of the customer's origin (x, y).
                    customer_dest (list): The coordinates of the customer's destination (x, y).

                Returns:
                    bool: True if the transport has enough autonomy and it was successfully decreased, False otherwise.
                """
        autonomy = self.get_autonomy()
        travel_km = self.calculate_km_expense(
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


