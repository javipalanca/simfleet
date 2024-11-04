import asyncio
import json
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
from simfleet.utils.status import CUSTOMER_LOCATION
from simfleet.common.lib.vehicles.models.vehicle import VehicleAgent

class TransportAgent(VehicleAgent):
    """
        TransportAgent is responsible for handling transport-related tasks, such as managing customer assignments,
        sending updates about travel status.
        It extends the VehicleAgent to include functionalities for managing current customers and service stations.

        Attributes:
            current_customer (dict): Stores information about the current assigned customer.
            num_assignments (int): Tracks the number of assignments completed.
            transport_type (str): Represents the type of transport (e.g., bus, taxi).
            customer_in_transport_event (asyncio.Event): Event that tracks when a customer boards the transport.
        """
    def __init__(self, agentjid, password):
        super().__init__(agentjid=agentjid, password=password)
        self.set("current_customer", {})
        self.num_assignments = 0
        self.transport_type = None

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

    def add_customer_in_transport(self, customer_id, origin=None, dest=None):
        """
            Adds a customer to the current transport and tracks their origin and destination.

            Args:
                customer_id (str): The ID of the customer.
                origin (list, optional): The starting point of the customer.
                dest (list, optional): The destination of the customer.
        """
        if customer_id is not str:
            customer_id = str(customer_id)

        self.get("current_customer")[str(customer_id)] = {"origin": origin, "dest": dest}

        self.num_assignments += 1

    def remove_customer_in_transport(self, customer_id):
        """
            Removes a customer from the current transport.

            Args:
                customer_id (str): The ID of the customer to remove.
        """
        if customer_id is not str:
            customer_id = str(customer_id)

        del self.get("current_customer")[customer_id]

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
        data = super().to_json()

        data.update({
            "assignments": self.num_assignments,
        })
        return data

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
