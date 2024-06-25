import asyncio
import json
import time
from asyncio import CancelledError
from collections import defaultdict

from loguru import logger
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from simfleet.utils.helpers import new_random_position
from simfleet.utils.utils_old import (
    CUSTOMER_WAITING,
    CUSTOMER_IN_DEST,
    TRANSPORT_MOVING_TO_CUSTOMER,
    CUSTOMER_IN_TRANSPORT,
    TRANSPORT_IN_CUSTOMER_PLACE,
    CUSTOMER_LOCATION,
    StrategyBehaviour,
    request_path,
    status_to_str,
)

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    TRAVEL_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    QUERY_PROTOCOL,
)

from simfleet.common.agents.customer import CustomerAgent
from simfleet.common.movable import MovableMixin

class BusCustomerAgent(MovableMixin, CustomerAgent):
#class BusCustomerAgent(CustomerAgent):
    def __init__(self, agentjid, password):
        CustomerAgent.__init__(self, agentjid, password)
        MovableMixin.__init__(self)

        # Bus line attributes
        self.__observers = defaultdict(list)
        self.current_stop = None
        self.destination_stop = None
        self.type_service = "stops"
        self.registered_in = None
        self.stop_dic = None
        self.in_transport_time = None
        self.total_sim_time = None
        self.alternative_transports = []

        #New atribute
        self.line = None
        self.arguments = {}

        # Transport in stop event
        self.set("arrived_to_destination", None)  # new
        self.customer_arrived_to_destination_event = asyncio.Event(loop=self.loop)

        def customer_arrived_to_destination_callback(old, new):
            if not self.customer_arrived_to_destination_event.is_set() and new is True:
                self.customer_arrived_to_destination_event.set()

        self.customer_arrived_to_destination_callback = customer_arrived_to_destination_callback

    def set_line(self, line):
        self.line = line

    def run_strategy(self):
        """import json
        Runs the strategy for the customer agent.
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            template2 = Template()
            template2.set_metadata("protocol", QUERY_PROTOCOL)
            self.add_behaviour(self.strategy(), template1 | template2)
            self.running_strategy = True

    # Bus line
    def get_waiting_time_bus(self):
        if self.waiting_for_pickup_time is not None:
            return self.waiting_for_pickup_time
        elif self.init_time is not None:
            if self.pickup_time is not None:
                return self.pickup_time - self.init_time
            else:
                return time.time() - self.init_time
        else:
            return None

    def in_transport_time_bus(self):
        if self.pickup_time:
            if self.end_time:
                return self.end_time - self.pickup_time
            else:
                return time.time() - self.pickup_time
        else:
            return None

    def get_waiting_for_pickup_time(self):
        return self.waiting_for_pickup_time

    def get_in_transport_time(self):
        return self.in_transport_time

    def get_total_sim_time(self):
        return self.total_sim_time

    def get_pickup_time(self):
        """
        Returns the time that the customer was waiting to be picked up since it has been assigned to a transport.

        Returns:
            float: The time that the customer was waiting to a transport since it has been assigned.
        """
        if self.pickup_time:
            return self.pickup_time - self.waiting_for_pickup_time
        return None


    def watch_value(self, key, callback):
        """
        Registers an observer callback to be run when a value is changed

        Args:
            key (str): the name of the value
            callback (function): a function to be called when the value changes. It receives two arguments: the old and the new value.
        """
        self.__observers[key].append(callback)


    async def set_position(self, coords=None):      #ANALIZAR CAMBIO - NOTAS
        """
        Sets the position of the customer. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        await super().set_position(coords)
        self.set("current_pos", coords)

        #if coords == self.dest:
        if self.is_in_destination():
            logger.success("Customer {} arrived to its destination {}".format(self.name, self.dest))
            self.status = CUSTOMER_IN_DEST
            self.set("arrived_to_destination", True)  # launch callback, awake FSMStrategyBehaviour
            self.end_time = time.time()


    async def setup(self):
        await super().setup()

        # ORIGINAL CODE - BUS
        # try:
        #     template = Template()
        #     template.set_metadata("protocol", TRAVEL_PROTOCOL)
        #     travel_behaviour = BusTravelBehaviour()
        #     self.add_behaviour(travel_behaviour, template)
        #     while not self.has_behaviour(travel_behaviour):
        #         logger.warning(
        #             "Customer {} could not create TravelBehaviour. Retrying...".format(
        #                 self.agent_id
        #             )
        #         )
        #         self.add_behaviour(travel_behaviour, template)
        #     self.ready = True
        # except Exception as e:
        #     logger.error(
        #         "EXCEPTION creating TravelBehaviour in Customer {}: {}".format(
        #             self.agent_id, e
        #         )
        #     )



# Bus line
class BusTravelBehaviour(CyclicBehaviour):
    """
    This is the internal behaviour that manages the movement of the customer.
    It is triggered when the transport informs the customer that it is going to the
    customer's position until the customer is dropped in its destination.
    """

    async def on_start(self):
        logger.debug("Customer {} started Bus Travel Behavior.".format(self.agent.name))

    async def run(self):
        try:
            msg = await self.receive(timeout=5)
            if not msg:
                return
            content = json.loads(msg.body)
            # logger.debug("Customer {} informed of: {}".format(self.agent.name, content))
            if "status" in content:
                status = content["status"]
                if status != CUSTOMER_LOCATION:
                    logger.debug(
                        "Customer {} informed of status: {}".format(
                            self.agent.name, status_to_str(status)
                        )
                    )
                if status == CUSTOMER_LOCATION:
                    coords = content["location"]
                    self.agent.set_position(coords)
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in Bus Travel Behaviour of Customer {}: {}".format(
                    self.agent.name, e
                )
            )
