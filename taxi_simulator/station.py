import logging
import json
import asyncio
from math import ceil
from spade.agent import Agent
from spade.template import Template
from spade.message import Message
from .utils import StrategyBehaviour, CyclicBehaviour, FREE_STATION, BUSY_STATION, TRANSPORT_MOVING_TO_STATION, TRANSPORT_IN_STATION_PLACE, \
    TRANSPORT_LOADED
from .protocol import REQUEST_PROTOCOL, REGISTER_PROTOCOL, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, REQUEST_PERFORMATIVE, TRAVEL_PROTOCOL, \
    CONFIRM_PERFORMATIVE
from .helpers import random_position

logger = logging.getLogger("StationAgent")


class StationAgent(Agent):
    def __init__(self, agentjid, password):
        super().__init__(jid=agentjid, password=password)
        self.agent_id = None
        self.secretary_id = None
        self.registration = False
        self.station_name = None
        self.type_station = None
        self.current_pos = None
        self.places_available = None
        self.status = None
        self.potency = None
        self.stopped = False

    async def setup(self):
        logger.info("Station agent running")
        self.set_type("Station")
        self.set_places_available(5)
        self.set_status()
        self.set_potency(50)
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

    def add_strategy(self, strategy_class):
        """
        Sets the strategy for the transport agent.

        Args:
            strategy_class (``RegistrationBehaviour``): The class to be used. Must inherit from ``RegistrationBehaviour``
        """
        template = Template()
        template.set_metadata("protocol", REQUEST_PROTOCOL)
        self.add_behaviour(strategy_class(), template)

    def set_registration(self, status):
        """
        Sets the status of registration
        Args:
            status (boolean): True if the transport agent has registered or False if not

        """
        self.registration = status

    def set_secretary(self, secretary_id):
        """
        Sets the secretary JID address
        Args:
            secretary_id (str): the SecretaryAgent jid

        """
        logger.debug("Asignacion del id de SecretaryAgent: {}".format(secretary_id))
        self.secretary_id = secretary_id

    def set_type(self, type):
        self.type_station = type

    async def set_position(self, coords=None):
        """
        Sets the position of the customer. If no position is provided it is located in a random position.

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

    def set_places_available(self, places):
        self.places_available = places

    def get_places_available(self):
        return self.places_available

    def set_potency(self, charge):
        self.potency = charge

    def get_potency(self):
        return self.potency

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
                    "potency": 10
                }
        """
        return {
            "id": self.agent_id,
            "position": self.current_pos,
            "status": self.status,
            "places": self.places_available,
            "potency": self.potency
        }

    def assigning_place(self):
        '''
        set a space in the charging station for the transport that has been accepted, when the available spaces are zero,
        the status will change to OCCUPATION STATION
        '''
        p = self.get_places_available()
        if not p-1:
            self.set_status(BUSY_STATION)
        self.set_places_available(p-1)

    def deassigning_place(self):
        '''
        leave a space of the charging station, when the station has free spaces, the status will change to FREE_STATION
        '''
        p = self.get_places_available()
        if p+1:
            self.set_status(FREE_STATION)
        self.set_places_available(p+1)

    async def loading_transport(self, fuel, batery_kW):
        total_time = ((batery_kW*1000)/(self.get_potency()*1000))*60
        t = ((100-fuel)/100)*total_time
        await asyncio.sleep(ceil(t/10))
        self.set("current_station", None)
        self.deassigning_place()


class RegistrationBehaviour(CyclicBehaviour):
    async def on_start(self):
        self.logger = logging.getLogger("SecretaryRegistrationStrategy")
        self.logger.debug("Strategy {} started in secretary".format(type(self).__name__))

    def set_registration(self, decision):
        self.agent.registration = decision

    async def run(self):
        try:
            msg = await self.receive(timeout=10)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == ACCEPT_PERFORMATIVE:
                    self.set_registration(True)
                    logger.info("Registration in the directory of secretary")
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
        '''
        Send a message to the transport agent that the vehicle load has been completed

        Args:
            transport_id (str): the jid of the transport
        '''
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
    Class from which to inherit to create a secretary strategy.
    You must overload the :func:`_process` method

    Helper functions:
        * :func:`get_transport_agents`
    """

    async def on_start(self):
        self.logger = logging.getLogger("StationStrategy")
        self.logger.debug("Strategy {} started in station".format(type(self).__name__))

    async def send_registration(self):
        """
        Send a ``spade.message.Message`` with a proposal to secretary to register.
        """
        logger.info("Station {} sent proposal to register to secretary {}".format(self.agent.name, self.agent.secretary_id))
        content = {
            "jid": str(self.agent.jid),
            "type": self.agent.type_station,
            "status": self.agent.status,
            "position": self.agent.get_position(),
            "charge": self.agent.potency
        }
        msg = Message()
        msg.to = str(self.agent.secretary_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

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
        self.agent.assigning_place()
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
        raise NotImplementedError
