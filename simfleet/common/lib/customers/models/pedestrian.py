from spade.template import Template

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    QUERY_PROTOCOL,
)

from simfleet.common.agents.customer import CustomerAgent
from simfleet.common.mixins.movable import MovableMixin

class PedestrianAgent(MovableMixin, CustomerAgent):
    def __init__(self, agentjid, password):
        CustomerAgent.__init__(self, agentjid, password)
        MovableMixin.__init__(self)

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

    async def set_position(self, coords=None):
        """
        Sets the position of the customer. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        await super().set_position(coords)
        self.set("current_pos", coords)
