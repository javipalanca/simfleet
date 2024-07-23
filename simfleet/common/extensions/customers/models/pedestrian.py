import asyncio
import json
import time
from asyncio import CancelledError
from collections import defaultdict

from loguru import logger
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
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

class PedestrianAgent(MovableMixin, CustomerAgent):
#class BusCustomerAgent(CustomerAgent):
    def __init__(self, agentjid, password):
        CustomerAgent.__init__(self, agentjid, password)
        MovableMixin.__init__(self)

        # Bus line attributes
        #self.__observers = defaultdict(list)
        #self.current_stop = None

        self.pedestrian_dest = None

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
