
import json

from loguru import logger
from asyncio import CancelledError

from spade.message import Message
from spade.template import Template
from spade.behaviour import CyclicBehaviour

from simfleet.common.movable import MovableMixin, MovingBehaviour
from simfleet.common.geolocatedagent import GeoLocatedAgent

from simfleet.utils.utils_old import StrategyBehaviour      #New vehicle

from simfleet.communications.protocol import (              #New vehicle
    REQUEST_PROTOCOL,
    REGISTER_PROTOCOL,
    ACCEPT_PERFORMATIVE,
    REQUEST_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
)

from simfleet.utils.utils_old import (                      #New vehicle
    VEHICLE_WAITING,
    VEHICLE_MOVING_TO_DESTINATION,
    VEHICLE_IN_DEST,
)

from simfleet.utils.helpers import AlreadyInDestination     #New vehicle

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

    #New vehicle
    async def setup(self):
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = VehicleRegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning(
                    "Vehicle {} could not create RegisterBehaviour. Retrying...".format(
                        self.agent_id
                    )
                )
                self.add_behaviour(register_behaviour, template)
            self.ready = True
        except Exception as e:
            logger.error(
                "EXCEPTION creating RegisterBehaviour in Vehicle {}: {}".format(
                    self.agent_id, e
                )
            )

    #New vehicle
    def run_strategy(self):
        """
        Runs the strategy for the vehicle agent.
        """
        if not self.running_strategy:
            template = Template()
            template.set_metadata("protocol", REQUEST_PROTOCOL)
            self.add_behaviour(self.strategy(), template)
            self.running_strategy = True

    #New vehicle
    async def set_position(self, coords=None):
        """
        Sets the position of the vehicle. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        #if coords:
        #    self.set("current_pos", coords)
        #else:
        #    self.set("current_pos", random_position())

        #logger.debug(
        #    "Transport {} position is {}".format(self.agent_id, self.get("current_pos"))
        #)

        super().set_position(coords)
        self.set("current_pos", coords)

        if self.is_in_destination():
            logger.info(
                "Vehicle {} has arrived to destination: {}. Position: {}".format(
                    self.agent_id, self.is_in_destination(), self.get("current_pos")
                )
            )
            if self.status == VEHICLE_MOVING_TO_DESTINATION:
                self.status = VEHICLE_IN_DEST

    #New vehicle
    def to_json(self):
        """
        Serializes the main information of a transport agent to a JSON format.
        It includes the id of the agent, its current position, the destination coordinates of the agent,
        the current status, the speed of the transport (in km/h), the path it is following (if any), the customer that it
        has assigned (if any), the number of assignments if has done and the distance that the transport has traveled.

        Returns:
            dict: a JSON doc with the main information of the transport.

            Example::

                {
                    "id": "cphillips",
                    "position": [ 39.461327, -0.361839 ],
                    "dest": [ 39.460599, -0.335041 ],
                    "status": 24,
                    "speed": 1000,
                    "path": [[0,0], [0,1], [1,0], [1,1], ...],
                    "customer": "ghiggins@127.0.0.1",
                    "assignments": 2,
                    "distance": 3481.34
                }
        """
        return {
            "id": self.agent_id,
            "position": [
                float("{0:.6f}".format(coord)) for coord in self.get("current_pos")
            ],
            "dest": [float("{0:.6f}".format(coord)) for coord in self.dest]
            if self.dest
            else None,
            "status": self.status,
            "speed": float("{0:.2f}".format(self.animation_speed))
            if self.animation_speed
            else None,
            "path": self.get("path")
            if self.get("current_customer")
            else None,
            "distance": "{0:.2f}".format(sum(self.distances)),
            "service": self.fleet_type,
            "icon": self.icon,
        }



#New vehicle
class VehicleRegistrationBehaviour(CyclicBehaviour):
    async def on_start(self):
        logger.debug("Strategy {} started in vehicle".format(type(self).__name__))

    async def run(self):
        try:
            msg = await self.receive(timeout=5)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == ACCEPT_PERFORMATIVE:
                    self.agent.set_registration(True)
                    logger.info("Registration in the dictionary of services")
                    self.agent.status = VEHICLE_WAITING
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in RegisterBehaviour of Manager {}: {}".format(
                    self.agent.name, e
                )
            )

#New vehicle
class VehicleStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a coordinator strategy.
    You must overload the :func:`_process` method

    """

    async def on_start(self):
        logger.debug("Strategy {} started in vehicle".format(type(self).__name__))

    async def send_registration(self):
        """
        Send a ``spade.message.Message`` with a proposal to directory to register.
        """
        logger.info(
            "Vehicle {} sent proposal to register to directory {}".format(
                self.agent.name, self.agent.directory_id
            )
        )

        content = {"jid": str(self.agent.jid), "type": self.agent.fleet_type}
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def planned_trip(self, dest=None):
        """
        It automatically launches the travelling process until the vehicle reaches
        the destination. This travelling process includes to update the transport coordinates as it
        moves along the path at the specified speed.

        Args:
            dest (list): the coordinates of the target destination of the vehicle
        """
        logger.info(
            "Vehicle {} on route to destination {}".format(self.agent.name, self.agent.dest)
        )
        self.agent.status = VEHICLE_MOVING_TO_DESTINATION
        try:
            logger.debug("{} move_to destination {}".format(self.agent.name, self.agent.dest))
            await self.agent.move_to(self.agent.dest)
        except AlreadyInDestination:
            logger.debug(
                "{} is already in the destination' {} position. . .".format(
                    self.agent.name, self.agent.dest
                )
            )
            self.agent.status = VEHICLE_IN_DEST

    async def run(self):
        raise NotImplementedError
