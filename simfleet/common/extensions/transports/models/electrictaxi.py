import json
import time

from loguru import logger

from spade.message import Message
from spade.behaviour import State

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    TRAVEL_PROTOCOL,
    PROPOSE_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    REGISTER_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    QUERY_PROTOCOL,
)

from simfleet.common.chargeable import ChargeableMixin
from simfleet.common.extensions.transports.models.taxi import TaxiAgent

class ElectricTaxiAgent(ChargeableMixin, TaxiAgent):
    def __init__(self, agentjid, password, **kwargs):
        ChargeableMixin.__init__(self)
        TaxiAgent.__init__(self, agentjid, password, **kwargs)

        self.stations = None
        self.current_station_dest = None
        self.set("current_station", None)

        self.arguments = {}


class ElectricTaxiStrategyBehaviour(State):
    """
    Class from which to inherit to create a transport strategy.
    You must overload the ```run`` coroutine

    Helper functions:
        * ``pick_up_customer``
        * ``send_proposal``
        * ``cancel_proposal``
    """

    async def on_start(self):
        # await super().on_start()
        logger.debug(
            "Strategy {} started in transport {}".format(
                type(self).__name__, self.agent.name
            )
        )

    async def on_end(self):
        # await super().on_start()
        logger.debug(
            "Strategy {} finished in transport {}".format(
                type(self).__name__, self.agent.name
            )
        )

    async def send_confirmation_travel(self, station_id):
        logger.info(
            "Transport {} sent confirmation to station {}".format(
                self.agent.name, station_id
            )
        )
        reply = Message()
        reply.to = station_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        await self.send(reply)

    async def go_to_the_station(self, station_id, dest):

        logger.info(
            "Transport {} on route to station {}".format(self.agent.name, station_id)
        )
        self.set("current_station", station_id)
        self.agent.current_station_dest = dest
        travel_km = self.agent.calculate_km_expense(self.get("current_pos"), dest)
        self.agent.set_km_expense(travel_km)

    async def request_access_station(self, station_id, content):

        if content is None:
            content = {}
        reply = Message()
        reply.to = station_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REQUEST_PERFORMATIVE)
        reply.body = json.dumps(content)
        logger.debug(
            "{} requesting access to {}".format(
                self.agent.name,
                station_id,
                reply.body
            )
        )
        await self.send(reply)

    async def send_get_stations(self, content=None):

        if content is None or len(content) == 0:
            content = self.agent.service_type

        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", QUERY_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = content
        await self.send(msg)

        logger.info(
            "Transport {} asked for stations to Directory {} for type {}.".format(
                self.agent.name, self.agent.directory_id, self.agent.service_type
            )
        )

    async def send_proposal(self, customer_id, content=None):
        """
        Send a ``spade.message.Message`` with a proposal to a customer to pick up him.
        If the content is empty the proposal is sent without content.

        Args:
            customer_id (str): the id of the customer
            content (dict, optional): the optional content of the message
        """
        if content is None:
            content = {}
        logger.info(
            "Transport {} sent proposal to {}".format(self.agent.name, customer_id)
        )
        reply = Message()
        reply.to = customer_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", PROPOSE_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def cancel_proposal(self, agent_id, content=None):
        """
        Send a ``spade.message.Message`` to cancel a proposal.
        If the content is empty the proposal is sent without content.

        Args:
            agent_id (str): the id of the customer
            content (dict, optional): the optional content of the message
        """
        if content is None:
            content = {}
        logger.info(
            "Transport {} sent cancel proposal to customer {}".format(
                self.agent.name, agent_id
            )
        )
        reply = Message()
        reply.to = agent_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def inform_station(self, data=None):
        """
        Sends a message to the current assigned customer to inform her about a new status.

        Args:
            status (int): The new status code
            data (dict, optional): complementary info about the status
        """
        if data is None:
            data = {}
        msg = Message()
        msg.to = self.get("current_station")
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        msg.body = json.dumps(data)
        await self.send(msg)

    async def comunicate_for_charging(self):

        # trigger charging
        self.agent.set("path", None)
        self.agent.chunked_path = None

        data = {
            "need": self.agent.max_autonomy_km - self.agent.current_autonomy_km,
        }

        logger.debug(
            "Transport {} with autonomy {} tells {} that it needs to charge "
            "{} km/autonomy".format(
                self.agent.agent_id,
                self.agent.current_autonomy_km,
                self.agent.get("current_station"),
                self.agent.max_autonomy_km - self.agent.current_autonomy_km,
            )
        )

        await self.agent.inform_station(data)

    async def drop_station(self):
        """
        Drops the customer that the transport is carring in the current location.
        """

        logger.debug(
            "Transport {} has dropped the station {}.".format(
                self.agent.agent_id, self.agent.get("current_station")
            )
        )
        self.agent.set("current_station", None)

    async def run(self):
        raise NotImplementedError
