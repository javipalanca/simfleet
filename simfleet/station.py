import asyncio
import json
import logging
from math import ceil

from spade.agent import Agent
from spade.message import Message
from spade.template import Template

from .helpers import random_position
from .protocol import REQUEST_PROTOCOL, REGISTER_PROTOCOL, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, \
    REQUEST_PERFORMATIVE, TRAVEL_PROTOCOL, CONFIRM_PERFORMATIVE, PROPOSE_PERFORMATIVE, CANCEL_PERFORMATIVE
from .utils import StrategyBehaviour, CyclicBehaviour, FREE_STATION, BUSY_STATION, TRANSPORT_MOVING_TO_STATION, \
    TRANSPORT_IN_STATION_PLACE, TRANSPORT_LOADED

logger = logging.getLogger("StationAgent")


class StationAgent(Agent):
    def __init__(self, agentjid, password):
        super().__init__(jid=agentjid, password=password)
        self.agent_id = None
        self.strategy = None
        self.running_strategy = False
        self.directory_id = None
        self.registration = False
        self.station_name = None
        self.station_type = None
        self.current_pos = None
        self.available_places = None
        self.status = None
        self.power = None
        self.stopped = False

    async def setup(self):
        logger.info("Station agent running")
        self.set_type("station")
        self.set_status()
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning("Station {} could not create RegisterBehaviour. Retrying...".format(self.agent_id))
                self.add_behaviour(register_behaviour, template)
        except Exception as e:
            logger.error("EXCEPTION creating RegisterBehaviour in Station {}: {}".format(self.agent_id, e))
        try:
            template = Template()
            template.set_metadata("protocol", TRAVEL_PROTOCOL)
            travel_behaviour = TravelBehaviour()
            self.add_behaviour(travel_behaviour, template)
            while not self.has_behaviour(travel_behaviour):
                logger.warning("Customer {} could not create TravelBehaviour. Retrying...".format(self.agent_id))
                self.add_behaviour(travel_behaviour, template)
        except Exception as e:
            logger.error("EXCEPTION creating TravelBehaviour in Customer {}: {}".format(self.agent_id, e))

    def set_id(self, agent_id):
        """
        Sets the agent identifier

        Args:
            agent_id (str): The new Agent Id
        """
        self.agent_id = agent_id

    def run_strategy(self):
        """
        Sets the strategy for the transport agent.

        Args:
            strategy_class (``RegistrationBehaviour``): The class to be used. Must inherit from ``RegistrationBehaviour``
        """
        if not self.running_strategy:
            template = Template()
            template.set_metadata("protocol", REQUEST_PROTOCOL)
            self.add_behaviour(self.strategy(), template)
            self.running_strategy = True

    def set_registration(self, status):
        """
        Sets the status of registration
        Args:
            status (boolean): True if the transport agent has registered or False if not

        """
        self.registration = status

    def set_directory(self, directory_id):
        """
        Sets the directory JID address
        Args:
            directory_id (str): the DirectoryAgent jid

        """
        self.directory_id = directory_id

    def set_type(self, station_type):
        self.station_type = station_type

    def set_position(self, coords=None):
        """
        Sets the position of the station. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        if coords:
            self.current_pos = coords
        else:
            self.current_pos = random_position()
        logger.debug("Customer {} position is {}".format(self.agent_id, self.current_pos))

    def get_position(self):
        """
        Returns the current position of the station.

        Returns:
            list: the coordinates of the current position of the customer (lon, lat)
        """
        return self.current_pos

    def set_status(self, state=FREE_STATION):
        self.status = state

    def get_status(self):
        return self.status

    def set_available_places(self, places):
        self.available_places = places

    def get_available_places(self):
        return self.available_places

    def set_power(self, charge):
        self.power = charge

    def get_power(self):
        return self.power

    def to_json(self):
        """
        Serializes the main information of a station agent to a JSON format.
        It includes the id of the agent, its current position, the destination coordinates of the agent,
        the current status, the transport that it has assigned (if any) and its waiting time.

        Returns:
            dict: a JSON doc with the main information of the station.

            Example::

                {
                    "id": "cphillips",
                    "position": [ 39.461327, -0.361839 ],
                    "status": True,
                    "places": 10,
                    "power": 10
                }
        """
        return {
            "id": self.agent_id,
            "position": self.current_pos,
            "status": self.status,
            "places": self.available_places,
            "power": self.power,
            "icon": "assets/img/station.png"
        }

    def assigning_place(self):
        """
        Set a space in the charging station for the transport that has been accepted, when the available spaces are zero,
        the status will change to BUSY_STATION
        """
        p = self.get_available_places()
        if not p - 1:
            self.set_status(BUSY_STATION)
        self.set_available_places(p - 1)

    def deassigning_place(self):
        """
        Leave a space of the charging station, when the station has free spaces, the status will change to FREE_STATION
        """
        p = self.get_available_places()
        if p + 1:
            self.set_status(FREE_STATION)
        self.set_available_places(p + 1)

    async def loading_transport(self, fuel, batery_kW):
        total_time = ((batery_kW * 1000) / (self.get_power() * 1000)) * 60
        t = ((100 - fuel) / 100) * total_time
        await asyncio.sleep(ceil(t / 10))
        self.set("current_station", None)
        self.deassigning_place()


class RegistrationBehaviour(CyclicBehaviour):
    async def on_start(self):
        self.logger = logging.getLogger("StationRegistrationStrategy")
        self.logger.debug("Strategy {} started in directory".format(type(self).__name__))

    def set_registration(self, decision):
        self.agent.registration = decision

    async def send_registration(self):
        """
        Send a ``spade.message.Message`` with a proposal to directory to register.
        """
        logger.info(
            "Station {} sent proposal to register to directory {}".format(self.agent.name, self.agent.directory_id))
        content = {
            "jid": str(self.agent.jid),
            "type": self.agent.station_type,
            "status": self.agent.status,
            "position": self.agent.get_position(),
            "charge": self.agent.power
        }
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def run(self):
        try:
            if not self.agent.registration:
                await self.send_registration()
            msg = await self.receive(timeout=10)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == ACCEPT_PERFORMATIVE:
                    self.set_registration(True)
                    logger.info("Registration in the directory")
        except Exception as e:
            logger.error("EXCEPTION in RegisterBehaviour of Station {}: {}".format(self.agent.name, e))


class TravelBehaviour(CyclicBehaviour):
    """
    This is the internal behaviour that manages the inform of the station.
    It is triggered when the transport informs the station that it is going to the
    customer's position until the customer is droppped in its destination.
    """

    async def on_start(self):
        logger.debug("Station {} started TravelBehavior.".format(self.agent.name))

    async def loading_completed(self, transport_id):
        """
        Send a message to the transport agent that the vehicle load has been completed

        Args:
            transport_id (str): the jid of the transport
        """
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CONFIRM_PERFORMATIVE)
        content = {"status": TRANSPORT_LOADED}
        reply.body = json.dumps(content)
        await self.send(reply)

    async def run(self):
        try:
            msg = await self.receive(timeout=5)
            if not msg:
                return
            content = json.loads(msg.body)
            transport_id = msg.sender
            logger.debug("Station {} informed of: {}".format(self.agent.name, content))
            if "status" in content:
                status = content["status"]
                if status == TRANSPORT_MOVING_TO_STATION:
                    logger.info("Transport goes to my destination.")
                elif status == TRANSPORT_IN_STATION_PLACE:
                    logger.info("Transport {} in Station.".format(msg.sender))
                    await self.agent.loading_transport(content["capacity"], content["batery"])
                    await self.loading_completed(transport_id)
        except Exception as e:
            logger.error("EXCEPTION in Travel Behaviour of Customer {}: {}".format(self.agent.name, e))


class StationStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a station strategy.
    You must overload the :func:`run` method

    Helper functions:
        * :func:`get_transport_agents`
    """

    async def on_start(self):
        self.logger = logging.getLogger("StationStrategy")
        self.logger.debug("Strategy {} started in station".format(type(self).__name__))

    async def accept_transport(self, transport_id):
        """
        Sends a ``spade.message.Message`` to a transport to accept a travel proposal for charge.
        It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

        Args:
            transport_id (str): The Agent JID of the transport
        """
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CONFIRM_PERFORMATIVE)
        content = {
            "station_id": str(self.agent.jid),
            "dest": self.agent.current_pos
        }
        reply.body = json.dumps(content)
        await self.send(reply)
        self.logger.debug("Station {} accepted proposal for charge from transport {}".format(self.agent.name,
                                                                                             transport_id))

    async def refuse_transport(self, transport_id):
        """
        Sends an ``spade.message.Message`` to a transport to refuse a travel proposal for charge.
        It uses the REQUEST_PROTOCOL and the REFUSE_PERFORMATIVE.

        Args:
            transport_id (str): The Agent JID of the transport
        """
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REFUSE_PERFORMATIVE)
        content = {}
        reply.body = json.dumps(content)

        await self.send(reply)
        self.logger.debug("Station {} refused proposal for charge from transport {}".format(self.agent.name,
                                                                                            transport_id))

    async def run(self):
        msg = await self.receive(timeout=5)

        if msg:
            performative = msg.get_metadata("performative")
            transport_id = msg.sender
            if performative == PROPOSE_PERFORMATIVE:
                if self.agent.get_status() == FREE_STATION:
                    self.logger.debug("Station {} received proposal from transport {}".format(self.agent.name,
                                                                                              transport_id))
                    await self.accept_transport(transport_id)
                else:  # self.agent.get_status() == BUSY_STATION
                    await self.refuse_transport(transport_id)
            elif performative == CANCEL_PERFORMATIVE:
                self.logger.warning(
                    "Station {} received a CANCEL from Transport {}.".format(self.agent.name, transport_id))
                self.agent.deassigning_place()
            elif performative == ACCEPT_PERFORMATIVE:
                self.agent.assigning_place()
