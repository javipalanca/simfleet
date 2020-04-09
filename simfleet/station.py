import datetime
import json
import time
from asyncio import CancelledError

from loguru import logger
from spade.agent import Agent
from spade.behaviour import TimeoutBehaviour
from spade.message import Message
from spade.template import Template

from .helpers import random_position
from .protocol import REQUEST_PROTOCOL, REGISTER_PROTOCOL, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, \
    REQUEST_PERFORMATIVE, TRAVEL_PROTOCOL, CANCEL_PERFORMATIVE, INFORM_PERFORMATIVE
from .utils import StrategyBehaviour, CyclicBehaviour, FREE_STATION, BUSY_STATION, TRANSPORT_MOVING_TO_STATION, \
    TRANSPORT_IN_STATION_PLACE, TRANSPORT_CHARGED


class StationAgent(Agent):
    def __init__(self, agentjid, password):
        super().__init__(jid=agentjid, password=password)
        self.agent_id = None
        self.icon = None
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
        self.ready = False

        # waiting waiting_list
        self.waiting_list = list()

        # statistics
        self.charged_transports = 0
        self.queue_length = 0
        self.max_queue_length = 0

        self.transports_in_queue_time = None
        self.empty_queue_time = None
        self.total_waiting_time = None

    async def setup(self):
        self.total_waiting_time = 0.0
        logger.info("Station agent {} running".format(self.name))
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
            logger.error("EXCEPTION creating TravelBehaviour in Station {}: {}".format(self.agent_id, e))
        self.ready = True

    async def send(self, msg):
        if not msg.sender:
            msg.sender = str(self.jid)
            logger.debug(f"Adding agent's jid as sender to message: {msg}")
        aioxmpp_msg = msg.prepare()
        await self.client.send(aioxmpp_msg)
        msg.sent = True
        self.traces.append(msg, category=str(self))

    def set_id(self, agent_id):
        """
        Sets the agent identifier

        Args:
            agent_id (str): The new Agent Id
        """
        self.agent_id = agent_id

    def set_icon(self, icon):
        self.icon = icon

    def run_strategy(self):
        """
        Sets the strategy for the transport agent.
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
            "icon": self.icon
        }

    async def assigning_place(self):
        """
        Set a space in the charging station for the transport that has been accepted, when the available spaces are zero,
        the status will change to BUSY_STATION
        """
        p = self.get_available_places()
        if p - 1 <= 0:
            self.set_status(BUSY_STATION)
        self.set_available_places(p - 1)
        logger.info("Station {} assigned place. Available places are now {}.".format(self.name,
                                                                                     self.get_available_places()))

    async def deassigning_place(self):
        """
        Leave a space of the charging station, when the station has free spaces, the status will change to FREE_STATION
        """
        if self.waiting_list:
            transport_id = self.waiting_list.pop(0)
            # time statistics update
            if len(self.waiting_list) == 0:
                self.empty_queue_time = time.time()
                self.total_waiting_time += self.empty_queue_time - self.transports_in_queue_time
            else:
                self.empty_queue_time = time.time()
                self.total_waiting_time += self.empty_queue_time - self.transports_in_queue_time
                self.transports_in_queue_time = time.time()

            logger.info(
                "-----------------Station {} has a place to charge transport {}".format(self.agent_id, transport_id))
            # confirm EXPLICITLY to transport it can start charging
            reply = Message()
            reply.to = str(transport_id)
            reply.set_metadata("protocol", REQUEST_PROTOCOL)
            reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
            content = {
                "station_id": self.agent_id
            }
            reply.body = json.dumps(content)
            await self.send(reply)
            # await send_confirmation_to_transport(transport_id)

        else:
            p = self.get_available_places()
            if p + 1:
                self.set_status(FREE_STATION)
            self.set_available_places(p + 1)

    async def charging_transport(self, need, transport_id):
        total_time = need / self.get_power()
        now = datetime.datetime.now()
        start_at = now + datetime.timedelta(seconds=total_time)
        logger.info(
            "Station {} started charging at {} for {} seconds, at {}".format(self.name, now, total_time, start_at))
        # charged transports update
        self.charged_transports += 1
        charge_behaviour = ChargeBehaviour(start_at=start_at, transport_id=transport_id)
        self.add_behaviour(charge_behaviour)


class ChargeBehaviour(TimeoutBehaviour):
    def __init__(self, start_at, transport_id):
        self.transport_id = transport_id
        super().__init__(start_at)

    async def charging_complete(self):
        """
        Send a message to the transport agent that the vehicle load has been completed
        """
        reply = Message()
        reply.to = str(self.transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        content = {"status": TRANSPORT_CHARGED}
        reply.body = json.dumps(content)
        await self.send(reply)

    async def run(self):
        logger.info("Station {} finished charging.".format(self.agent.name))
        self.set("current_station", None)
        await self.agent.deassigning_place()
        await self.charging_complete()


class RegistrationBehaviour(CyclicBehaviour):
    async def on_start(self):
        logger.debug("Strategy {} started in directory".format(type(self).__name__))

    def set_registration(self, decision):
        self.agent.registration = decision

    async def send_registration(self):
        """
        Send a ``spade.message.Message`` with a proposal to directory to register.
        """
        logger.debug(
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
                    logger.debug("Registration in the directory")
        except CancelledError:
            logger.debug("Cancelling async tasks...")
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
                    logger.info("Transport {} coming to station {}.".format(transport_id, self.agent.name))
                elif status == TRANSPORT_IN_STATION_PLACE:
                    # logger.info("Transport {} in station {}.".format(msg.sender.localpart, self.agent.name))
                    logger.info(
                        "Station {} is going to start charging transport {}".format(self.agent.name, transport_id))
                    await self.agent.charging_transport(content["need"], transport_id)
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error("EXCEPTION in Travel Behaviour of Station {}: {}".format(self.agent.name, e))


class StationStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a station strategy.
    You must overload the :func:`run` method

    Helper functions:
        * :func:`get_transport_agents`
    """

    async def on_start(self):
        logger.debug("Strategy {} started in station".format(type(self).__name__))

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
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        content = {
            "station_id": str(self.agent.jid),
            "dest": self.agent.current_pos
        }
        reply.body = json.dumps(content)
        await self.send(reply)
        logger.debug("Station {} accepted proposal for charge from transport {}".format(self.agent.name, transport_id))

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
        logger.debug("Station {} refused proposal for charge from transport {}".format(self.agent.name, transport_id))

    async def run(self):
        msg = await self.receive(timeout=5)

        if msg:
            performative = msg.get_metadata("performative")
            transport_id = msg.sender
            if performative == CANCEL_PERFORMATIVE:
                logger.warning("Station {} received a CANCEL from Transport {}.".format(self.agent.name, transport_id))
                await self.agent.deassigning_place()
            elif performative == ACCEPT_PERFORMATIVE:  # comes from send_confirmation_travel
                if self.agent.get_status() == FREE_STATION:
                    logger.info("Station {} has a place to charge transport {}".format(self.agent.name, transport_id))
                    # confirm EXPLICITLY to transport it can start charging
                    reply = Message()
                    reply.to = str(transport_id)
                    reply.set_metadata("protocol", REQUEST_PROTOCOL)
                    reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
                    content = {
                        "station_id": self.agent.name
                    }
                    reply.body = json.dumps(content)
                    await self.send(reply)
                    await self.agent.assigning_place()
                    # self.agent.assigning_place()

                else:  # self.agent.get_status() == BUSY_STATION
                    # time statistics update
                    if len(self.agent.waiting_list) == 0:
                        self.agent.transports_in_queue_time = time.time()
                    # transport waits in a waiting_list until it is available to charge
                    self.agent.waiting_list.append(str(transport_id))
                    # list length statistics update
                    self.agent.queue_length = len(self.agent.waiting_list)
                    if self.agent.queue_length > self.agent.max_queue_length:
                        self.agent.max_queue_length = self.agent.queue_length
                    # logger.warning("********************{} waiting in {} waiting_list".format(transport_id, self.agent.name))
                    logger.info("{} waiting at {}, whose waiting list is {}".format(transport_id, self.agent.name,
                                                                                    self.agent.waiting_list))

                    # change refuse_transport
                    # await self.refuse_transport(transport_id)
