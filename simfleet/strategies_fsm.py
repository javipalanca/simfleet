import asyncio

from loguru import logger
from spade.behaviour import State, FSMBehaviour

#from simfleet.common.agents.customer import CustomerStrategyBehaviour
from simfleet.common.agents.fleetmanager import FleetManagerStrategyBehaviour
from simfleet.common.vehicle import VehicleStrategyBehaviour    #New vehicle
from simfleet.utils.helpers import PathRequestException, AlreadyInDestination
#from simfleet.common.agents.transport import TransportStrategyBehaviour        #transport.py

from simfleet.utils.utils_old import (
    VEHICLE_WAITING,
    VEHICLE_MOVING_TO_DESTINATION,
    VEHICLE_IN_DEST,
)


################################################################
#                                                              #
#                     FleetManager Strategy                    #
#                                                              #
################################################################
class DelegateRequestBehaviour(FleetManagerStrategyBehaviour):
    """
    The default strategy for the FleetManager agent. By default it delegates all requests to all transports.
    """

    async def run(self):
        if not self.agent.registration:
            await self.send_registration()

        msg = await self.receive(timeout=5)
        logger.debug("Manager received message: {}".format(msg))
        if msg:
            for transport in self.get_transport_agents().values():
                msg.to = str(transport["jid"])
                logger.debug(
                    "Manager sent request to transport {}".format(transport["name"])
                )
                await self.send(msg)




################################################################
#                                                              #
#                     Vehicle Strategy                         #
#                                                              #
################################################################
#class RequestAndTravelBehavior(VehicleStrategyBehaviour):
#    """
#    The default strategy for the Vehicle agent. By default it register and move agent to the destination.
#    """

#    async def run(self):

#        if self.agent.status != None and self.agent.status == VEHICLE_WAITING:
#            try:
#                logger.debug(
#                    "Transport {} continue the trip".format(
#                        self.agent.name
#                    )
#                )

#                await self.planned_trip()
#                return
#            except PathRequestException:
#                logger.error(
#                    "Transport {} could not get a path to customer. Cancelling...".format(
#                        self.agent.name
#                    )
#                )
#                return


class DumbVehicleWaitingState(VehicleStrategyBehaviour, State):
    async def on_start(self):
        await super().on_start()
        self.agent.status = VEHICLE_WAITING
        logger.debug("{} in Vehicle Waiting State".format(self.agent.jid))

    async def run(self):
        if self.agent.status != None and self.agent.status == VEHICLE_WAITING:
            #logger.warning("Vehicle Waiting State")
            try:
                logger.debug(
                    "Vehicle {} continue the trip".format(
                        self.agent.name
                    )
                )
                await self.planned_trip()
                self.set_next_state(VEHICLE_MOVING_TO_DESTINATION)
                return
            except PathRequestException:
                logger.error(
                    "Transport {} could not get a path to customer. Cancelling...".format(
                        self.agent.name
                    )
                )
                self.set_next_state(VEHICLE_WAITING)
                return

class DumbVehicleMovingState(VehicleStrategyBehaviour, State):
    async def on_start(self):
        await super().on_start()
        self.agent.status = VEHICLE_MOVING_TO_DESTINATION
        logger.debug("{} in Vehicle Moving State".format(self.agent.jid))

    async def run(self):
        #logger.warning("VEHICULO vehicle_arrived: {}".format(self.vehicle_arrived()))
        #logger.warning("Vehicle Moving State")
        try:
            #await self.vehicle_arrived()

            if not self.agent.is_in_destination():
                await asyncio.sleep(1)
                self.set_next_state(VEHICLE_MOVING_TO_DESTINATION)
            else:
                self.set_next_state(VEHICLE_IN_DEST)
                #await self.planned_trip()
            #return
        #except PathRequestException:
        except AlreadyInDestination:
            logger.warning(
                "Vehicle {} has arrived to destination: {}.".format(
                    self.agent.agent_id, self.agent.is_in_destination()
                )
            )
            self.agent.status = VEHICLE_IN_DEST
            self.set_next_state(VEHICLE_IN_DEST)
            return
        except PathRequestException:
            logger.error(
                "Transport {} could not get a path to customer. Cancelling...".format(
                    self.agent.name
                )
            )
            self.agent.status = VEHICLE_WAITING
            self.set_next_state(VEHICLE_WAITING)
            return


class DumbVehicleInDestState(VehicleStrategyBehaviour, State):
    async def on_start(self):
        await super().on_start()
        self.agent.status = VEHICLE_IN_DEST
        logger.debug("{} in Vehicle Moving State".format(self.agent.jid))

    async def run(self):
        logger.info("{} arrived at its destination".format(self.agent.jid))
        #self.set_next_state(VEHICLE_IN_DEST)


class FSMDumbVehicleStrategyBehaviour(FSMBehaviour):
    def setup(self):
        # Create states
        self.add_state(VEHICLE_WAITING, DumbVehicleWaitingState(), initial=True)
        self.add_state(VEHICLE_MOVING_TO_DESTINATION, DumbVehicleMovingState())
        self.add_state(VEHICLE_IN_DEST, DumbVehicleInDestState())

        # Create transitions
        self.add_transition(
            VEHICLE_WAITING, VEHICLE_WAITING
        )  # waiting for messages
        self.add_transition(
            VEHICLE_WAITING, VEHICLE_MOVING_TO_DESTINATION
        )  # accepted by customer

        self.add_transition(
            VEHICLE_MOVING_TO_DESTINATION, VEHICLE_MOVING_TO_DESTINATION
        )  # transport refused
        self.add_transition(
            VEHICLE_MOVING_TO_DESTINATION, VEHICLE_WAITING
        )  # transport refused
        self.add_transition(
            VEHICLE_MOVING_TO_DESTINATION, VEHICLE_IN_DEST
        )  # going to pick up customer
