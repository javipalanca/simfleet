import json
from loguru import logger

from spade.message import Message
from spade.behaviour import State

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    PROPOSE_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    REQUEST_PERFORMATIVE,
)

from simfleet.common.mixins.chargeable import ChargeableMixin
from simfleet.common.lib.transports.models.taxi import TaxiAgent

class ElectricTaxiAgent(ChargeableMixin, TaxiAgent):
    """
        Represents an electric taxi agent with enhanced functionalities for managing charging stations,
        nearby station selection, and other electric vehicle-specific features.
        This class extends the capabilities of `TaxiAgent` and integrates charging functionality
        through the `ChargeableMixin`.

        Attributes:
            stations (list): A list of available charging stations.
            nearby_station (tuple): The ID and position of the nearest charging station.
            arguments (dict): Additional custom arguments for the access to station agent.

        Methods:
            set_stations(stations):
                Sets the list of available charging stations.
            get_stations():
                Retrieves the list of available charging stations.
            get_number_stations():
                Gets the total number of charging stations.
            set_nearby_station(station):
                Sets the nearest charging station.
            get_nearby_station():
                Retrieves the nearest charging station.
            get_nearby_station_id():
                Retrieves the ID of the nearest charging station.
            get_nearby_station_position():
                Retrieves the position of the nearest charging station.
        """
    def __init__(self, agentjid, password, **kwargs):
        ChargeableMixin.__init__(self)
        TaxiAgent.__init__(self, agentjid, password, **kwargs)

        self.stations = None
        self.nearby_station = None
        self.set("current_station", None)

        self.arguments = {}

    async def setup(self):
        await super().setup()

    def set_stations(self, stations):
        """
               Set the list of charging stations.

               Args:
                   stations (list): A list of charging station details.
        """
        self.stations = stations

    def get_stations(self):
        """
                Retrieve the list of charging stations.

                Returns:
                    list: A list of charging station details.
        """
        return self.stations

    def get_number_stations(self):
        """
                Retrieve the number of available charging stations.

                Returns:
                    int: The number of charging stations in the list.
        """
        return len(self.stations)

    def set_nearby_station(self, station):
        """
                Set the nearest charging station.

                Args:
                    station (tuple): A tuple containing the ID and position of the station.
        """
        self.nearby_station = station

    def get_nearby_station(self):
        """
                Retrieve the nearest charging station.

                Returns:
                    tuple: A tuple containing the JID and position of the nearest charging station.
        """
        return self.nearby_station

    def get_nearby_station_id(self):
        """
                Retrieve the ID of the nearest charging station.

                Returns:
                    Any: The ID of the nearest charging station.
        """
        return self.nearby_station[0]

    def get_nearby_station_position(self):
        """
                Retrieve the position of the nearest charging station.

                Returns:
                    Any: The position of the nearest charging station.
        """
        return self.nearby_station[1]




class ElectricTaxiStrategyBehaviour(State):
    """
    Base class to define the transport strategy for an electric taxi.
    This class should be inherited and extended to create custom strategies.
    Subclasses must override the `run` coroutine to define specific behaviors.

    Methods:
        async on_start():
            Logs the beginning of the strategy execution.
        async on_end():
            Logs the end of the strategy execution.
        async go_to_the_station(station_id, dest):
            Directs the taxi to a specific station and updates autonomy based on distance.
        check_and_decrease_autonomy(customer_orig, customer_dest):
            Checks if there is enough autonomy for a trip and decreases it if possible.
        async drop_station():
            Resets the current station assignment for the taxi.
        async request_access_station(station_id, content):
            Sends a request to a station for access.
        async send_proposal(customer_id, content=None):
            Sends a transport proposal to a customer.
        async cancel_proposal(agent_id, content=None):
            Cancels a previously sent proposal to a customer.
        async run():
            Abstract method that must be implemented by subclasses.
    """

    async def on_start(self):
        """
                Logs the beginning of the strategy execution.
                """
        # await super().on_start()
        logger.debug(
            "Agent[{}]: Strategy {} started.".format(
                self.agent.name, type(self).__name__
            )
        )

    async def on_end(self):
        """
                Logs the end of the strategy execution.
                """
        # await super().on_start()
        logger.debug(
            "Agent[{}]: Strategy {} finished.".format(
                self.agent.name, type(self).__name__
            )
        )

    async def go_to_the_station(self, station_id, dest):
        """
                Directs the taxi to a specific station and updates autonomy based on the distance.

                Args:
                    station_id (str): The ID of the destination station.
                    dest (list): The coordinates of the station (x, y).
                """
        logger.info(
            "Agent[{}]: On route to station [{}]".format(self.agent.name, station_id)
        )
        self.set("current_station", station_id)
        #self.agent.current_station_dest = dest
        travel_km = self.agent.calculate_km_expense(self.get("current_pos"), dest)
        self.agent.decrease_autonomy_km(travel_km)

    def check_and_decrease_autonomy(self, customer_orig, customer_dest):
        """
        Verifies if the ttransport has enough autonomy for a trip and decreases autonomy if possible.

        Args:
            customer_orig (list): The customer's origin coordinates (x, y).
            customer_dest (list): The customer's destination coordinates (x, y).

        Returns:
            bool: True if autonomy is sufficient and decreased, False otherwise.
        """

        if self.agent.has_enough_autonomy(customer_orig, customer_dest):
            autonomy = self.agent.get_autonomy()
            travel_km = self.agent.calculate_km_expense(
                self.agent.get_position(), customer_orig, customer_dest
            )
            self.agent.decrease_autonomy_km(travel_km)
            return True
        else:
            return False

    async def drop_station(self):
        """
        Resets the current station assignment for the transport.
        """

        logger.debug(
            "Agent[{}]: The agent has dropped the station [{}].".format(
                self.agent.agent_id, self.agent.get("current_station")
            )
        )
        self.agent.set("current_station", None)

    async def request_access_station(self, station_id, content):

        """
                Sends a request to a station for access.

                Args:
                    station_id (str): The ID of the station to request access from.
                    content (dict): Additional information to include in the request.
                """

        if content is None:
            content = {}
        reply = Message()
        reply.to = station_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REQUEST_PERFORMATIVE)
        reply.body = json.dumps(content)
        logger.debug(
            "Agent[{}]: The agent requesting access to [{}]".format(
                self.agent.name,
                station_id,
                reply.body
            )
        )
        await self.send(reply)

    async def send_proposal(self, customer_id, content=None):
        """
        Sends a proposal to a customer offering transport.

        Args:
            customer_id (str): The ID of the customer.
            content (dict, optional): Additional content for the proposal. Defaults to None.
        """
        if content is None:
            content = {}
        logger.info(
            "Agent[{}]: The agent sent proposal to agent [{}]".format(self.agent.name, customer_id)
        )
        reply = Message()
        reply.to = customer_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", PROPOSE_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def cancel_proposal(self, agent_id, content=None):
        """
        Cancels a previously sent proposal.

        Args:
            agent_id (str): The ID of the customer.
            content (dict, optional): Additional content for the cancellation. Defaults to None.
        """
        if content is None:
            content = {}
        logger.info(
            "Agent[{}]: The agent sent cancel proposal to agent [{}]".format(
                self.agent.name, agent_id
            )
        )
        reply = Message()
        reply.to = agent_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)


    async def run(self):
        raise NotImplementedError
