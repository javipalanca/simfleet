import asyncio
import json
import sys
import time
from asyncio import CancelledError

from loguru import logger
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    TRAVEL_PROTOCOL,
    CANCEL_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    REGISTER_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    QUERY_PROTOCOL,
)
from simfleet.utils.utils_old import (
    TRANSPORT_WAITING,
    TRANSPORT_IN_STATION_PLACE,
    TRANSPORT_CHARGING,
    CUSTOMER_LOCATION,
    TRANSPORT_NEEDS_CHARGING,
)
from simfleet.common.extensions.vehicles.models.vehicle import VehicleAgent

class TransportAgent(VehicleAgent):
    """
        TransportAgent is responsible for handling transport-related tasks, such as managing customer assignments,
        sending updates about travel status.
        It extends the VehicleAgent to include functionalities for managing current customers and service stations.

        Attributes:
            current_customer (dict): Stores information about the current assigned customer.
            num_assignments (int): Tracks the number of assignments completed.
            transport_type (str): Represents the type of transport (e.g., bus, taxi).
            request (str): Specifies the type of request (default is "station").
            stations (list): List of available stations for the transport.
            num_charges (int): Counter for the number of times the transport was charged.
            current_station (str): The current station assigned to the transport.
            current_station_dest (str): The destination station for charging or refueling.
            transport_in_station_place_event (asyncio.Event): Event that tracks when the transport arrives at the station.
            customer_in_transport_event (asyncio.Event): Event that tracks when a customer boards the transport.
        """
    def __init__(self, agentjid, password):
        super().__init__(agentjid=agentjid, password=password)
        self.set("current_customer", {})
        self.num_assignments = 0
        self.transport_type = None                              # nuevo para JSON
        self.request = "station"
        self.stations = None
        self.num_charges = 0
        self.set("current_station", None)
        self.current_station_dest = None

        self.transport_in_station_place_event = asyncio.Event(loop=self.loop)

        def transport_in_station_place_callback(old, new):
            if not self.transport_in_station_place_event.is_set() and new is True:
                self.transport_in_station_place_event.set()

        self.transport_in_station_place_callback = transport_in_station_place_callback

        # Customer in transport event
        self.customer_in_transport_event = asyncio.Event(loop=self.loop)

        def customer_in_transport_callback(old, new):
            # if event flag is False and new is None
            if not self.customer_in_transport_event.is_set() and new is None:
                # Sets event flag to True, all coroutines waiting for it are awakened
                self.customer_in_transport_event.set()

        self.customer_in_transport_callback = customer_in_transport_callback

    async def setup(self):
        """
            Sets up the transport agent, registers it with the fleet manager, and ensures that
            the agent has the required behaviors for communication.
        """
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning(
                    "Transport {} could not create RegisterBehaviour. Retrying...".format(
                        self.agent_id
                    )
                )
                self.add_behaviour(register_behaviour, template)
            self.ready = True
        except Exception as e:
            logger.error(
                "EXCEPTION creating RegisterBehaviour in Transport {}: {}".format(
                    self.agent_id, e
                )
            )

    def sleep(self, seconds):
        # await asyncio.sleep(seconds)
        time.sleep(seconds)

    def run_strategy(self):
        """
        Sets the strategy for the transport agent.

        Args:
            strategy_class (TransportStrategyBehaviour): The class to be used. Must inherit from `TransportStrategyBehaviour`.
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            template2 = Template()
            template2.set_metadata("protocol", QUERY_PROTOCOL)
            self.add_behaviour(self.strategy(), template1 | template2)
            self.running_strategy = True

    async def send(self, msg):
        """
            Sends a message via the XMPP protocol, ensuring the sender is correctly set.

            Args:
                msg (Message): The message to send.
        """
        if not msg.sender:
            msg.sender = str(self.jid)
            logger.debug(f"Adding agent's jid as sender to message: {msg}")
        aioxmpp_msg = msg.prepare()
        await self.client.send(aioxmpp_msg)
        msg.sent = True
        self.traces.append(msg, category=str(self))


    async def inform_customer(self, customer_id, status, data=None):
        """
        Sends a message to inform the customer of the transport's new status.

        Args:
            customer_id (str): The ID of the customer.
            status (int): The new status code.
            data (dict, optional): Additional information about the status.
        """
        if data is None:
            data = {}
        msg = Message()
        msg.to = customer_id
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        data["status"] = status
        msg.body = json.dumps(data)
        await self.send(msg)

    async def inform_customer_moving(self, customer_id, status, data=None):
        """
        Sends a message to the customer to inform them of the transport's movement.

        Args:
            customer_id (str): The ID of the customer.
            status (int): The new status code.
            data (dict, optional): Additional movement-related information.
        """
        if data is None:
            data = {}
        msg = Message()
        #msg.to = self.get("current_customer")
        msg.to = customer_id
        msg.set_metadata("protocol", TRAVEL_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        data["status"] = status
        msg.body = json.dumps(data)
        await self.send(msg)

    async def cancel_customer(self, customer_id, data=None):
        """
        Cancels the assignment of a customer and informs them via a message.

        Args:
            customer_id (str): The ID of the customer.
            data (dict, optional): Additional cancellation-related information.
        """
        logger.error(
            "Transport {} could not get a path to customer {}.".format(
                self.agent_id, self.get("current_customer")
            )
        )
        if data is None:
            data = {}
        reply = Message()
        reply.to = customer_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        reply.body = json.dumps(data)
        logger.debug(
            "Transport {} sent cancel proposal to customer {}".format(
                self.agent_id, customer_id
            )
        )
        await self.send(reply)

    async def add_customer_in_transport(self, customer_id, origin=None, dest=None):
        """
            Adds a customer to the current transport and tracks their origin and destination.

            Args:
                customer_id (str): The ID of the customer.
                origin (list, optional): The starting point of the customer.
                dest (list, optional): The destination of the customer.
        """
        customers = self.get("current_customer")
        customers[customer_id] = {"origin": origin, "destination": dest}
        self.set("current_customer", customers)
        self.num_assignments += 1

    async def remove_customer_in_transport(self, customer_id):
        """
            Removes a customer from the current transport.

            Args:
                customer_id (str): The ID of the customer to remove.
        """
        customers = self.get("current_customer")
        del customers[customer_id]
        self.set("current_customer", customers)

    async def set_position(self, coords=None):
        """
        Sets the transport's position and updates customers with the new location.

        Args:
            coords (list, optional): Coordinates to set as the new position.
        """

        await super().set_position(coords)
        self.set("current_pos", coords)

        if len(self.get("current_customer")) > 0:
            for key, item in self.get("current_customer").items():
                await self.inform_customer_moving(
                    customer_id=key, status=CUSTOMER_LOCATION,
                    data={"location": self.get("current_pos")}
                )

    def to_json(self):
        """
        Serializes the main information of a transport agent to a JSON format.
        It includes the id of the agent, its current position, the destination coordinates of the agent,
        the current status, the speed of the transport (in km/h), the path it is following (if any), the customer that it
        has assigned (if any), the number of assignments if has done and the distance that the transport has traveled.

        Returns:
            dict: a JSON doc with the main information of the transport.

            Example::

                {
                    "id": "cphillips",
                    "position": [ 39.461327, -0.361839 ],
                    "dest": [ 39.460599, -0.335041 ],
                    "status": 24,
                    "speed": 1000,
                    "path": [[0,0], [0,1], [1,0], [1,1], ...],
                    "customer": "ghiggins@127.0.0.1",
                    "assignments": 2,
                    "distance": 3481.34
                }
        """
        # MOD-STRATEGY-02 - modify
        customers = self.get("current_customer")
        if len(customers) != 0:
            customer_id = next(iter(customers.items()))[0]
        else:
            customer_id = None

        return {
            "id": self.agent_id,
            "position": [
                float("{0:.6f}".format(coord)) for coord in self.get("current_pos")
            ],
            "dest": [float("{0:.6f}".format(coord)) for coord in self.dest]
            if self.dest
            else None,
            "status": self.status,
            "speed": float("{0:.2f}".format(self.animation_speed))
            if self.animation_speed
            else None,
            "path": self.get("path"),
            #"customer": self.get("current_customer").split("@")[0]         # MOD-STRATEGY-02 - modify
            #if self.get("current_customer")                                # MOD-STRATEGY-02 - modify
            "customer": customer_id.split("@")[0]
            if customer_id
            else None,
            "assignments": self.num_assignments,
            "distance": "{0:.2f}".format(sum(self.distances)),
            #"autonomy": self.current_autonomy_km,          #CHANGE THE to_json with inheritance
            #"autonomy": self.current_autonomy_km
            #if self.current_autonomy_km
            #else None,
            #"max_autonomy": self.max_autonomy_km,          #CHANGE THE to_json with inheritance
            #"max_autonomy": self.max_autonomy_km
            #if self.max_autonomy_km
            #else None,
            "service": self.fleet_type,
            "fleet": self.fleetmanager_id.split("@")[0]
            if self.fleetmanager_id
            else None,
            "icon": self.icon,
        }

class RegistrationBehaviour(CyclicBehaviour):
    async def on_start(self):
        logger.debug("Strategy {} started in transport".format(type(self).__name__))

    async def send_registration(self):
        """
        Send a ``spade.message.Message`` with a proposal to manager to register.
        """
        logger.debug(
            "Transport {} sent proposal to register to manager {}".format(
                self.agent.name, self.agent.fleetmanager_id
            )
        )
        content = {
            "name": self.agent.name,
            "jid": str(self.agent.jid),
            "fleet_type": self.agent.fleet_type,
        }
        msg = Message()
        msg.to = str(self.agent.fleetmanager_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def run(self):
        try:
            if not self.agent.registration and self.agent.fleetmanager_id!=None:
                await self.send_registration()
            msg = await self.receive(timeout=10)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == ACCEPT_PERFORMATIVE:
                    content = json.loads(msg.body)
                    self.agent.set_registration(True, content)
                    logger.info(
                        "[{}] Registration in the fleet manager accepted: {}.".format(
                            self.agent.name, self.agent.fleetmanager_id
                        )
                    )
                    self.kill(exit_code="Fleet Registration Accepted")
                elif performative == REFUSE_PERFORMATIVE:
                    logger.warning(
                        "Registration in the fleet manager was rejected (check fleet type)."
                    )
                    self.kill(exit_code="Fleet Registration Rejected")
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in RegisterBehaviour of Transport {}: {}".format(
                    self.agent.name, e
                )
            )
