import logging
import json
from spade.agent import Agent
from spade.template import Template
from spade.message import Message
from .utils import StrategyBehaviour, CyclicBehaviour
from .protocol import REQUEST_PROTOCOL, REGISTER_PROTOCOL, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, REQUEST_PERFORMATIVE
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
        self.charge_time = None
        self.stopped = False

    async def setup(self):
        logger.info("Station agent running")
        self.set_type("Station")
        self.set_places_available(5)
        self.set_status()
        self.set_charge_time(35)
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

    def set_status(self, state=True):
        self.status = state

    def get_status(self):
        return self.status

    def set_places_available(self, places):
        self.places_available = places

    def get_places_available(self):
        return self.places_available

    def set_charge_time(self, charge):
        self.charge_time = charge

    def get_charge_time(self):
        return self.charge_time

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
                    "charge_time": 10
                }
        """
        return {
            "id": self.agent_id,
            "position": self.current_pos,
            "status": self.status,
            "places": self.places_available,
            "charge_time": self.charge_time
        }


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
            "state": self.agent.status,
            "position": self.agent.get_position(),
            "charge": self.agent.charge_time
        }
        msg = Message()
        msg.to = str(self.agent.secretary_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def run(self):
        raise NotImplementedError
