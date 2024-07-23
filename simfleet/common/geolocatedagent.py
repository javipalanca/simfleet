import json
import geopy.distance
from loguru import logger

from spade.message import Message
from spade.template import Template
from spade.behaviour import OneShotBehaviour

from simfleet.common.simfleetagent import SimfleetAgent

from simfleet.utils.helpers import new_random_position, distance_in_meters#, random_position
from simfleet.communications.protocol import COORDINATION_PROTOCOL, INFORM_PERFORMATIVE, QUERY_PROTOCOL, REQUEST_PERFORMATIVE, CANCEL_PERFORMATIVE

class GeoLocatedAgent(SimfleetAgent):
    def __init__(self, agentjid, password):
        super().__init__(agentjid, password)
        self.route_host = None                                          #transport.py
        self.set("current_pos", None)                        #transport.py
        self.boundingbox = None                                         #New boundingbox

        self.icon = None                                                #transport.py

    #Used TransportAgent - CustomerAgent - StationAgent - FleetMaganerAgent (different)
    def set_icon(self, icon):
        self.icon = icon

    #Used TransportAgent - CustomerAgent
    def set_route_host(self, route_host):
        """
        Sets the route host server address
        Args:
            route_host (str): the route host server address

        """
        self.route_host = route_host

    #Used TransportAgent (hija) - CustomerAgent
    def set_position(self, coords=None):
        """
        Sets the position of the Agent. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        #logger.debug("1)Agent {} position is {}".format(self.agent_id, coords))

        if coords:
            #self.current_pos = coords      #Non-parallel variable - Used customer.py
            self.set("current_pos", coords)
        else:
            #self.current_pos = random_position()       #Non-parallel variable - Used customer.py
            #self.set("current_pos", random_position())
            self.set("current_pos", new_random_position(self.boundingbox, self.route_host))
        logger.debug(
            "Agent {} position is {}".format(self.agent_id, self.get("current_pos"))
        )

    #Used TransportAgent
    def set_initial_position(self, coords):
        #self.set("current_pos", coords)
        if coords:
            #self.current_pos = coords      #Non-parallel variable - Used customer.py
            self.set("current_pos", coords)
        else:
            #self.current_pos = random_position()       #Non-parallel variable - Used customer.py
            self.set("current_pos", new_random_position(self.boundingbox, self.route_host))

    #Used TransportAgent - CustomerAgent - StationAgent
    def get_position(self):
        """
        Returns the current position of the Agent.

        Returns:
            list: the coordinates of the current position of the Agent (lon, lat)
        """
        return self.get("current_pos")

    def near_agent(self, coords_1, coords_2):
        if geopy.distance.geodesic(coords_1, coords_2).km > 0.1:  #Añadir rango 100 metros min
            return False
        return True

    #New funtion - Nearst agent - Pedestrian, ElectricTaxi, Delivery - A utils
    def nearst_agent(self, agent_list, position):

        agent_positions = []
        for key in agent_list.keys():
            dic = agent_list.get(key)
            agent_positions.append((dic["jid"], dic["position"]))

        closest_agent = min(
            agent_positions,
            #key=lambda x: distance_in_meters(x[1], self.get_position()),   #Original
            key=lambda x: distance_in_meters(x[1], position),
        )
        logger.debug("Closest agent {}".format(closest_agent))
        agent = closest_agent[0]
        result = (
            agent,
            agent_list[agent]["position"],
        )
        logger.info(
            "Transport {} selected station {}.".format(self.name, agent)
        )
        return result

    # New boundingbox
    def set_boundingbox(self, bbox):
        self.boundingbox = bbox

    async def get_list_agent_position(self, agent_type, agent_list):

        # NEW LIST POSITION
        template1 = Template()
        template1.set_metadata("protocol", QUERY_PROTOCOL)
        template1.set_metadata("performative", INFORM_PERFORMATIVE)

        template2 = Template()
        template2.set_metadata("protocol", QUERY_PROTOCOL)
        template2.set_metadata("performative", CANCEL_PERFORMATIVE)

        instance = GetListOfAgentPosition(agent_type, agent_list)
        self.add_behaviour(instance, template1 | template2)

        await instance.join()  # Wait for the behaviour to complete

        return instance.agent_list
    #def to_json(self):
    #    """
    #    Returns a JSON with the relevant data of this type of agent
    #    """
    #    data = super().to_json()
    #    data.update({
    #        "position": [
    #            float(coord) for coord in self.get("current_pos")
    #        ],
    #        "icon": self.icon
    #    })
    #    return data

class GetListOfAgentPosition(OneShotBehaviour):
    def __init__(self, agent_type, agent_list):
        super().__init__()

        self.agent_type = agent_type
        self.agent_list = agent_list


    async def send_get_agents(self, content=None):
        """
        Sends an ``spade.message.Message`` to the DirectoryAgent to request the list of stops in the system.
        It uses the QUERY_PROTOCOL and the REQUEST_PERFORMATIVE.
        If no content is set a default content with the type_service that needs
        Args:
            content (dict): Optional content dictionary
        """
        if content is None or len(content) == 0:
            content = self.agent_type
            logger.warning(
                "The message has no content: {}".format(
                    content
                )
            )

        msg = Message()
        msg.to = str(self.agent.directory_id)
        #msg.to = self.agent.directory_id
        msg.set_metadata("protocol", QUERY_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = content
        await self.send(msg)

        logger.info(
            "Agent {} asked for stops to directory {} for type {}.".format(
                self.agent.name, self.agent.directory_id, self.agent_type
            )
        )


    async def run(self):

        if self.agent_list is None:
            await self.send_get_agents(self.agent_type)

            msg = await self.receive(timeout=300)  # Mensaje del director con las paradas
            if msg:
                protocol = msg.get_metadata("protocol")
                if protocol == QUERY_PROTOCOL:
                    performative = msg.get_metadata("performative")
                    if performative == INFORM_PERFORMATIVE:
                        self.agent_list = json.loads(msg.body)
                        logger.debug(
                            "Customer {} got stops from directory: {}".format(
                                self.agent.name, self.agent_list
                            )
                        )
                        #self.setup_stops()
                    elif performative == CANCEL_PERFORMATIVE:
                        logger.warning(
                            "{} got cancellation of request for {} information".format(
                                self.agent.name, self.agent_type
                            )
                        )
