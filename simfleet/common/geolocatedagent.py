import json
import geopy.distance
from loguru import logger

from spade.message import Message
from spade.template import Template
from spade.behaviour import OneShotBehaviour

from simfleet.common.simfleetagent import SimfleetAgent

from simfleet.utils.helpers import new_random_position, distance_in_meters
from simfleet.communications.protocol import INFORM_PERFORMATIVE, QUERY_PROTOCOL, REQUEST_PERFORMATIVE, CANCEL_PERFORMATIVE

class GeoLocatedAgent(SimfleetAgent):
    """
        GeoLocatedAgent is a base class for agents that need to handle geographic location. It inherits from
        SimfleetAgent and adds methods for setting, getting, and managing the position of an agent on the map.

        Attributes:
            route_host (str): The host of the route service used for requesting paths.
            boundingbox (tuple): The bounding box coordinates that define the area where the agent can be placed.
            icon (str): The visual representation or icon of the agent.
    """
    def __init__(self, agentjid, password):
        super().__init__(agentjid, password)
        self.route_host = None
        self.set("current_pos", None)
        self.boundingbox = None

        self.icon = None


    def set_icon(self, icon):
        """
            Sets the icon for the agent.

            Args:
                icon (str): The icon representing the agent.
        """
        self.icon = icon


    def set_route_host(self, route_host):
        """
        Sets the route host server address for requesting paths.

        Args:
            route_host (str): The route host server address.
        """
        self.route_host = route_host


    def set_position(self, coords=None):
        """
        Sets the position of the agent. If no position is provided, the agent's position is randomized within its bounding box.

        Args:
            coords (list): A list of coordinates [longitude, latitude].
        """

        if coords:
            self.set("current_pos", coords)
        else:
            self.set("current_pos", new_random_position(self.boundingbox, self.route_host))
        logger.debug(
            "Agent[{}]: The agent position is ({})".format(self.agent_id, self.get("current_pos"))
        )

    def set_initial_position(self, coords=None):
        """
            Sets the initial position of the agent. If no coordinates are provided, a random position is generated.

            Args:
                coords (list): A list of coordinates [longitude, latitude].
        """
        if coords:
            self.set("current_pos", coords)
        else:
            self.set("current_pos", new_random_position(self.boundingbox, self.route_host))

    def get_position(self):
        """
        Retrieves the current position of the agent.

        Returns:
            list: The current coordinates of the agent (longitude, latitude).
        """
        return self.get("current_pos")

    def to_json(self):
        data = super().to_json()  # Call to to_json of SimfleetAgent
        data.update({
            "position": [float("{0:.6f}".format(coord)) for coord in self.get("current_pos")],
            "icon": self.icon,
        })
        return data

    def near_agent(self, coords_1, coords_2):
        """
            Determines if two agents are near each other, within 100 meters.

            Args:
                coords_1 (list): The coordinates of the first agent.
                coords_2 (list): The coordinates of the second agent.

            Returns:
                bool: True if the agents are near each other, False otherwise.
        """
        if geopy.distance.geodesic(coords_1, coords_2).km > 0.1:
            return False
        return True


    def nearst_agent(self, agent_list, position):
        """
            Finds the closest agent from a list of agents to the specified position.

            Args:
                agent_list (dict): A dictionary of agents with their positions.
                position (list): The position to compare against.

            Returns:
                tuple: The closest agent's JID and position.
        """

        agent_positions = []
        for key in agent_list.keys():
            dic = agent_list.get(key)
            agent_positions.append((dic["jid"], dic["position"]))

        closest_agent = min(
            agent_positions,
            key=lambda x: distance_in_meters(x[1], position),
        )
        logger.debug("Closest agent {}".format(closest_agent))
        agent = closest_agent[0]
        result = (
            agent,
            agent_list[agent]["position"],
        )
        logger.info(
            "Agent[{}]: The agent selected agent ({}).".format(self.name, agent)
        )
        return result

    def set_boundingbox(self, bbox):
        """
            Sets the bounding box within which the agent operates.

            Args:
                bbox (tuple): A bounding box defining the area of operations for the agent.
        """
        self.boundingbox = bbox

    async def get_list_agent_position(self, agent_type, agent_list):
        """
            Requests the list of agents of a given type from the directory agent and waits for the response.

            Args:
                agent_type (str): The type of agent being requested (e.g., 'bus stop', 'station').
                agent_list (dict): The current list of agents.

            Returns:
                dict: A list of agent positions, updated after the request.
        """

        # NEW LIST POSITION
        template1 = Template()
        template1.set_metadata("protocol", QUERY_PROTOCOL)
        template1.set_metadata("performative", INFORM_PERFORMATIVE)

        template2 = Template()
        template2.set_metadata("protocol", QUERY_PROTOCOL)
        template2.set_metadata("performative", CANCEL_PERFORMATIVE)

        instance = GetListOfAgentPosition(agent_type, agent_list)
        self.add_behaviour(instance, template1 | template2)

        # Wait for the behaviour to complete
        await instance.join()

        return instance.agent_list

class GetListOfAgentPosition(OneShotBehaviour):
    """
        This class handles the behavior of requesting a list of agent positions from the directory agent.

        Attributes:
            agent_type (str): The type of agent being requested.
            agent_list (dict): The list of agents.
    """
    def __init__(self, agent_type, agent_list):
        super().__init__()

        self.agent_type = agent_type
        self.agent_list = agent_list


    async def send_get_agents(self, content=None):
        """
            Sends a message to the directory agent to request a list of agents of a specific type.

            Args:
                content (dict): Optional content to be included in the request message.
        """
        if content is None or len(content) == 0:
            content = self.agent_type
            logger.warning(
                "Agent[{}]: The message has no content: {}".format(
                    self.agent.name,
                    content
                )
            )

        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", QUERY_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = content
        await self.send(msg)

        logger.info(
            "Agent[{}]: The agent asked for services to directory [{}] for type ({}).".format(
                self.agent.name, self.agent.directory_id, self.agent_type
            )
        )


    async def run(self):
        """
            Executes the behavior to request and receive the list of agent positions.
        """
        if self.agent_list is None:
            await self.send_get_agents(self.agent_type)

            msg = await self.receive(timeout=300)
            if msg:
                protocol = msg.get_metadata("protocol")
                if protocol == QUERY_PROTOCOL:
                    performative = msg.get_metadata("performative")
                    if performative == INFORM_PERFORMATIVE:
                        self.agent_list = json.loads(msg.body)
                        logger.debug(
                            "Agent[{}]: The agent got services from directory: {}".format(
                                self.agent.name, self.agent_list
                            )
                        )
                    elif performative == CANCEL_PERFORMATIVE:
                        logger.warning(
                            "Agent[{}]: THe agent got cancellation of request for ({}) information".format(
                                self.agent.name, self.agent_type
                            )
                        )
