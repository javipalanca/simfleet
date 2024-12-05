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

        # Customer in transport event
        self.customer_in_transport_event = asyncio.Event(loop=self.loop)

        def customer_in_transport_callback(old, new):
            # if event flag is False and new is None
            if not self.customer_in_transport_event.is_set() and new is None:
                # Sets event flag to True, all coroutines waiting for it are awakened
                self.customer_in_transport_event.set()

        self.customer_in_transport_callback = customer_in_transport_callback


    async def setup(self):
        await super().setup()


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
            "Agent[{}]: The agent could not get a path to customer [{}].".format(
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
            "Agent[{}]: The agent sent cancel proposal to customer [{}]".format(
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

        self.num_assignments -= 1

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


