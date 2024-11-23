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

    Methods:
        __init__():
            Initializes the mixin with default values for autonomy and charging time.
        set_service_type(service_type):
            Sets the type of service the transport provides.
        set_autonomy(autonomy, current_autonomy=None):
            Sets the maximum and current autonomy of the transport.
        get_autonomy():
            Retrieves the current autonomy of the vehicle.
        decrease_autonomy_km(expense=0):
            Reduces the current autonomy based on the travel expense.
        increase_autonomy_km(expense=0):
            Increases the current autonomy based on a given value.
        increase_full_autonomy_km():
            Fully recharges the transport vehicle, restoring its autonomy to the maximum value.
        calculate_km_expense(current_pos, origin, dest=None):
            Calculates the travel distance (in kilometers) for a trip.
        has_enough_autonomy(orig, dest):
            Checks if the transport has enough autonomy to complete a trip.
    """

    def __init__(self):
        """
                Initializes the mixin with default values for autonomy and charging time.
        """

        self.current_autonomy_km = 2000
        self.max_autonomy_km = 2000
        self.service_type = None


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



    def decrease_autonomy_km(self, expense=0):
        """
                Reduces the current autonomy based on the travel expense.

                Args:
                    expense (int): The distance in kilometers to subtract from the current autonomy.
                """
        if self.current_autonomy_km - expense > 0:
            self.current_autonomy_km -= expense
        else:
            self.current_autonomy_km = 0

        logger.debug(
            "Agent [{}]: The max autonomy is ({}), and the current autonomy is ({}).".format(self.name,
                                                                                                 self.max_autonomy_km,
                                                                                                 self.current_autonomy_km)
        )

    def increase_autonomy_km(self, expense=0):
        """
                Increases the current autonomy by a specified value, capped at the maximum autonomy.

                Args:
                    expense (int): The amount to increase the current autonomy.
                """
        if expense + self.current_autonomy_km < self.max_autonomy_km:
            self.current_autonomy_km += expense
        else:
            self.current_autonomy_km = self.max_autonomy_km

        logger.debug(
            "Agent [{}]: The max autonomy is ({}), and the current autonomy is ({}).".format(self.name,
                                                                                             self.max_autonomy_km,
                                                                                             self.current_autonomy_km)
        )

    def increase_full_autonomy_km(self):
        """
            Fully recharges the transport vehicle, restoring its autonomy to the maximum value.
        """
        self.current_autonomy_km = self.max_autonomy_km
        logger.debug(
            "Agent [{}]: The max autonomy is ({}), and the current autonomy is ({}).".format(self.name,
                                                                                                 self.max_autonomy_km,
                                                                                                 self.current_autonomy_km)
        )

    def calculate_km_expense(self, current_pos, origin, dest=None):
        """
        Calculates the travel distance (in kilometers) for a trip.

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

    def has_enough_autonomy(self, orig, dest):
        """
        Checks if the transport has enough autonomy to complete a trip from the agent's origin to the destination.

        Args:
            orig (list): The coordinates of the agent's origin (x, y).
            dest (list): The coordinates of the agent's destination (x, y).

        Returns:
            bool: True if the transport has enough autonomy, False otherwise.
        """
        autonomy = self.get_autonomy()
        if autonomy <= MIN_AUTONOMY:
            logger.warning(
                "Agent[{}]: Has not enough autonomy ({}).".format(self.name, autonomy)
            )
            return False
        travel_km = self.calculate_km_expense(
            self.get_position(), orig, dest
        )
        logger.debug(
            "Agent[{}]: Has autonomy ({}) when max autonomy is ({})"
            " and needs ({}) for the trip".format(
                self.name,
                self.get_autonomy(),
                self.max_autonomy_km,
                travel_km,
            )
        )

        if autonomy - travel_km < MIN_AUTONOMY:
            logger.warning(
                "Agent[{}]: Has not enough autonomy to do travel ({} for {} km).".format(
                    self.name, autonomy, travel_km
                )
            )
            return False
        return True



