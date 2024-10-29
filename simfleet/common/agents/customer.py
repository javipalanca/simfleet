import json
import time
from asyncio import CancelledError

from loguru import logger
from spade.behaviour import CyclicBehaviour
from spade.template import Template

from simfleet.utils.helpers import new_random_position
from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    TRAVEL_PROTOCOL,
    QUERY_PROTOCOL,
)
from simfleet.utils.utils_old import (
    CUSTOMER_LOCATION,
)

from simfleet.common.geolocatedagent import GeoLocatedAgent


class CustomerAgent(GeoLocatedAgent):
    """
        CustomerAgent is responsible for representing customers in the simulation. It handles tasks such as
        requesting transport, tracking their destination, and interacting with assigned transport agents.

        Attributes:
            customer_dest (list): The destination coordinates of the customer.
    """
    def __init__(self, agentjid, password):
        super().__init__(agentjid, password)

        self.customer_dest = None

    async def setup(self):
        """
            Sets up the customer agent, ensuring that the agent is prepared for travel by creating the required
            behaviours and assigning a travel strategy.
        """
        try:
            template = Template()
            template.set_metadata("protocol", TRAVEL_PROTOCOL)
            travel_behaviour = TravelBehaviour()
            self.add_behaviour(travel_behaviour, template)
            while not self.has_behaviour(travel_behaviour):
                logger.warning(
                    "Customer {} could not create TravelBehaviour. Retrying...".format(
                        self.agent_id
                    )
                )
                self.add_behaviour(travel_behaviour, template)
            self.ready = True
        except Exception as e:
            logger.error(
                "EXCEPTION creating TravelBehaviour in Customer {}: {}".format(
                    self.agent_id, e
                )
            )

    def run_strategy(self):
        """
        Runs the strategy for the customer agent by creating behaviours for requesting and querying transports.
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            template2 = Template()
            template2.set_metadata("protocol", QUERY_PROTOCOL)
            self.add_behaviour(self.strategy(), template1 | template2)
            self.running_strategy = True

    def set_target_position(self, coords=None):
        """
        Sets the target position of the customer (i.e., its destination).
        If no position is provided, the destination is set to a random position.

        Args:
            coords (list): A list of coordinates (longitude and latitude) for the destination.
        """
        if coords:
            self.customer_dest = coords
        else:
            self.customer_dest = new_random_position(self.boundingbox, self.route_host)
        logger.debug(
            "Customer {} target position is {}".format(self.agent_id, self.customer_dest)
        )

    async def set_position(self, coords=None):
        """
        Sets the current position of the customer. If no coordinates are provided, the customer is
        placed at a random position.

        Args:
            coords (list): A list of coordinates (longitude and latitude) representing the customer's position.
        """
        super().set_position(coords)
        self.set("current_pos", coords)

    def to_json(self):
        data = super().to_json()
        data.update({
            "dest": [float("{0:.6f}".format(coord)) for coord in self.customer_dest],
        })
        return data


class TravelBehaviour(CyclicBehaviour):
    """
    The TravelBehaviour class manages the movement of the customer agent. It triggers when the assigned
    transport informs the customer about its arrival and continues until the customer reaches their destination.

    Attributes:
        timeout (int): The timeout value for receiving a message from the transport.
    """

    async def on_start(self):
        """
            Called when the behaviour is started. Logs a message indicating the customer has started travel.
        """
        logger.debug("Customer {} started TravelBehavior.".format(self.agent.name))

    async def run(self):
        """
            Continuously runs, checking for messages from the transport. Upon receiving information
            (such as new coordinates or status), it updates the customer’s position.
        """
        try:
            msg = await self.receive(timeout=5)
            if not msg:
                return
            content = json.loads(msg.body)
            logger.debug("Customer {} informed of: {}".format(self.agent.name, content))
            if "status" in content:
                status = content["status"]
                if status == CUSTOMER_LOCATION:
                    coords = content["location"]
                    await self.agent.set_position(coords)
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in Travel Behaviour of Customer {}: {}".format(
                    self.agent.name, e
                )
            )

