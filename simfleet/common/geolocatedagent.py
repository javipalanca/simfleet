from loguru import logger

from simfleet.common.simfleetagent import SimfleetAgent

from simfleet.utils.helpers import new_random_position#, random_position

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

    # New boundingbox
    def set_boundingbox(self, bbox):
        self.boundingbox = bbox

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
