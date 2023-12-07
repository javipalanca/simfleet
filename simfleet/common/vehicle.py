
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
