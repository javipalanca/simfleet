from loguru import logger

from simfleet.common.simfleetagent import SimfleetAgent

from simfleet.utils.helpers import random_position

class GeoLocatedAgent(SimfleetAgent):
    def __init__(self, agentjid, password):
        super().__init__(agentjid, password)
        self.route_host = None                                          #transport.py
        self.set("current_pos", None)                        #transport.py

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



    #Used TransportAgent
    def set_initial_position(self, coords):
        self.set("current_pos", coords)

    #Used TransportAgent - CustomerAgent - StationAgent
    def get_position(self):
        """
        Returns the current position of the Agent.

        Returns:
            list: the coordinates of the current position of the Agent (lon, lat)
        """
        return self.get("current_pos")

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
