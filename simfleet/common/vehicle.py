from loguru import logger

from simfleet.common.movable import MovableMixin, MovingBehaviour
from simfleet.common.geolocatedagent import GeoLocatedAgent


class VehicleAgent(MovableMixin, GeoLocatedAgent):
    def __init__(self, agentjid, password):
        GeoLocatedAgent.__init__(self, agentjid, password)
        MovableMixin.__init__(self)

        self.fleetmanager_id = None                     #transport.py
        #self.registration = None
        #self.current_autonomy_km = 2000                 #transport.py
        #self.max_autonomy_km = 2000                     #transport.py

    def set_fleetmanager(self, fleetmanager_id):
        """
        Sets the fleetmanager JID address
        Args:
            fleetmanager_id (str): the fleetmanager jid

        """
        logger.info(
            "Setting fleet {} for agent {}".format(
                fleetmanager_id.split("@")[0], self.name
            )
        )
        self.fleetmanager_id = fleetmanager_id
