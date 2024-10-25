import json

from loguru import logger
from asyncio import CancelledError

from spade.message import Message
from spade.template import Template
from spade.behaviour import CyclicBehaviour, State

from simfleet.common.movable import MovableMixin
from simfleet.common.geolocatedagent import GeoLocatedAgent
#

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    REGISTER_PROTOCOL,
    ACCEPT_PERFORMATIVE,
    REQUEST_PERFORMATIVE,
)

from simfleet.utils.helpers import AlreadyInDestination

class VehicleAgent(MovableMixin, GeoLocatedAgent):
    """
        The VehicleAgent class represents a vehicle in the system. It inherits from both MovableMixin and GeoLocatedAgent,
        combining the functionality of movement and geolocation. This agent can register with a fleet manager, move to a
        destination, and execute strategies defined by specific behaviors.

        Attributes:
            fleetmanager_id (str): The ID of the fleet manager the vehicle is registered with.
    """
    def __init__(self, agentjid, password):
        """
            Initializes the VehicleAgent with its unique JID and password. The vehicle agent also has attributes
            to store the fleet manager's ID and manages its own state regarding its location and registration.

            Args:
                agentjid (str): The Jabber ID of the agent.
                password (str): The password used for agent authentication.
        """
        GeoLocatedAgent.__init__(self, agentjid, password)
        MovableMixin.__init__(self)

        self.fleetmanager_id = None

    def set_fleetmanager(self, fleetmanager_id):
        """
        Sets the fleet manager's JID for the vehicle.

        Args:
            fleetmanager_id (str): The JID of the fleet manager to be set for this vehicle.
        """
        logger.info(
            "Setting fleet {} for agent {}".format(
                fleetmanager_id.split("@")[0], self.name
            )
        )
        self.fleetmanager_id = fleetmanager_id

    async def setup(self):
        """
            Sets up the vehicle agent by registering a behavior that handles the vehicle's registration process.
            The vehicle will attempt to register with the directory and fleet manager upon setup.
        """
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

            if not self.registration:
                await self.send_registration()

        except Exception as e:
            logger.error(
                "EXCEPTION creating RegisterBehaviour in Vehicle {}: {}".format(
                    self.agent_id, e
                )
            )

    def run_strategy(self):
        """
        Runs the strategy for the vehicle agent. It initializes the behavior associated with the vehicle's operations
        and begins executing its assigned strategy.
        """
        if not self.running_strategy:
            template = Template()
            template.set_metadata("protocol", REQUEST_PROTOCOL)
            self.add_behaviour(self.strategy(), template)
            self.running_strategy = True


    async def set_position(self, coords=None):
        """
        Sets the vehicle's position. If no position is provided, the vehicle will be assigned a random position.

        Args:
            coords (list): A list of coordinates representing the vehicle's longitude and latitude.
        """

        super().set_position(coords)
        self.set("current_pos", coords)


    async def send_registration(self):
        """
        Sends a registration request to the directory to register the vehicle. The vehicle sends its JID and type to
        the directory for registration purposes.
        """
        logger.info(
            "Vehicle {} sent proposal to register to directory {}".format(
                self.name, self.directory_id
            )
        )

        content = {"jid": str(self.jid), "type": self.fleet_type}
        msg = Message()
        msg.to = str(self.directory_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

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


class VehicleRegistrationBehaviour(CyclicBehaviour):
    """
        This behavior handles the registration process of the vehicle agent. It listens for registration responses
        and manages the registration lifecycle of the vehicle within the system.
    """
    async def on_start(self):
        """
                Logs the start of the registration strategy for the vehicle.
        """
        logger.debug("Strategy {} started in vehicle".format(type(self).__name__))

    async def run(self):
        """
            Waits for registration responses and processes them. If the registration is accepted, the vehicle sets
            itself as registered.
        """
        try:
            msg = await self.receive(timeout=5)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == ACCEPT_PERFORMATIVE:
                    self.agent.set_registration(True)
                    logger.info("Registration in the dictionary of services")

        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in RegisterBehaviour of Manager {}: {}".format(
                    self.agent.name, e
                )
            )

class VehicleStrategyBehaviour(State):
    """
    This class defines the vehicle's behavior strategy. It is designed to be extended to implement
    custom strategies for vehicle operations.

    Key Methods:
        - on_start(): Logs the initialization of the strategy.
        - planned_trip(): Defines how the vehicle should move to its destination.
    """

    async def on_start(self):
        """
            Logs the start of the vehicle's strategy behavior.
        """
        logger.debug("Strategy {} started in vehicle".format(type(self).__name__))

    async def planned_trip(self, dest=None):
        """
        Initiates the process for the vehicle to travel to the specified destination. The vehicle moves along the
        path, updating its position until it reaches its destination.

        Args:
            dest (list): The coordinates of the vehicle's destination.
        """
        logger.info(
            "Vehicle {} on route to destination {}".format(self.agent.name, self.agent.dest)
        )
        try:
            logger.debug("{} move_to destination {}".format(self.agent.name, self.agent.dest))
            await self.agent.move_to(self.agent.dest)
        except AlreadyInDestination:
            logger.debug(
                "{} is already in the destination' {} position. . .".format(
                    self.agent.name, self.agent.dest
                )
            )

    async def run(self):
        """
            Abstract method that should be implemented in subclasses. This is where the specific strategy of the
            vehicle will be executed.
        """
        raise NotImplementedError
