import asyncio

from loguru import logger
from spade.behaviour import State, FSMBehaviour

from simfleet.common.lib.vehicles.models.vehicle import VehicleStrategyBehaviour
from simfleet.utils.helpers import PathRequestException, AlreadyInDestination
from simfleet.utils.utils_old import VEHICLE_WAITING, VEHICLE_MOVING_TO_DESTINATION, VEHICLE_IN_DEST
from simfleet.utils.abstractstrategies import FSMStrategyBehaviour


################################################################
#                                                              #
#                   OneShot Vehicle Strategy                   #
#                                                              #
################################################################

class OneShotVehicleWaitingState(VehicleStrategyBehaviour):
    async def on_start(self):
        await super().on_start()
        self.agent.status = VEHICLE_WAITING
        logger.debug("{} in Vehicle Waiting State".format(self.agent.jid))

    async def run(self):
        if self.agent.status != None and self.agent.status == VEHICLE_WAITING:

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


class OneShotVehicleMovingState(VehicleStrategyBehaviour):
    async def on_start(self):
        await super().on_start()
        self.agent.status = VEHICLE_MOVING_TO_DESTINATION
        logger.debug("{} in Vehicle Moving State".format(self.agent.jid))

    async def run(self):
        try:

            if not self.agent.is_in_destination():
                await asyncio.sleep(1)
                self.set_next_state(VEHICLE_MOVING_TO_DESTINATION)
            else:
                self.set_next_state(VEHICLE_IN_DEST)

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


class OneShotVehicleInDestState(VehicleStrategyBehaviour):
    async def on_start(self):
        await super().on_start()
        self.agent.status = VEHICLE_IN_DEST
        logger.debug("{} in Vehicle Moving State".format(self.agent.jid))

    async def run(self):
        logger.info("{} arrived at its destination".format(self.agent.jid))


class FSMOneShotVehicleStrategyBehaviour(FSMStrategyBehaviour):
    def setup(self):
        # Create states
        self.add_state(VEHICLE_WAITING, OneShotVehicleWaitingState(), initial=True)
        self.add_state(VEHICLE_MOVING_TO_DESTINATION, OneShotVehicleMovingState())
        self.add_state(VEHICLE_IN_DEST, OneShotVehicleInDestState())

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


################################################################
#                                                              #
#                   Cycle Vehicle Strategy                     #
#                                                              #
################################################################

class CycleVehicleWaitingState(VehicleStrategyBehaviour):
    async def on_start(self):
        await super().on_start()
        self.agent.status = VEHICLE_WAITING
        logger.debug("{} in Vehicle Waiting State".format(self.agent.jid))

    async def run(self):
        if self.agent.status != None and self.agent.status == VEHICLE_WAITING:
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


class CycleVehicleMovingState(VehicleStrategyBehaviour):
    async def on_start(self):
        await super().on_start()
        self.agent.status = VEHICLE_MOVING_TO_DESTINATION
        logger.debug("{} in Vehicle Moving State".format(self.agent.jid))

    async def run(self):
        try:

            if not self.agent.is_in_destination():
                await asyncio.sleep(1)
                self.set_next_state(VEHICLE_MOVING_TO_DESTINATION)
            else:
                self.set_next_state(VEHICLE_IN_DEST)

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


class CycleVehicleInDestState(VehicleStrategyBehaviour):
    async def on_start(self):
        await super().on_start()
        self.agent.status = VEHICLE_IN_DEST
        logger.debug("{} in Vehicle Moving State".format(self.agent.jid))

    async def run(self):
        logger.info("{} arrived at its destination".format(self.agent.jid))

        logger.debug("{} processes a new destination address".format(self.agent.jid))
        self.agent.set_target_position()
        self.agent.status = VEHICLE_WAITING
        self.set_next_state(VEHICLE_WAITING)
        return

class FSMCycleVehicleStrategyBehaviour(FSMStrategyBehaviour):
    def setup(self):
        # Create states
        self.add_state(VEHICLE_WAITING, CycleVehicleWaitingState(), initial=True)
        self.add_state(VEHICLE_MOVING_TO_DESTINATION, CycleVehicleMovingState())
        self.add_state(VEHICLE_IN_DEST, CycleVehicleInDestState())

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
        self.add_transition(
            VEHICLE_IN_DEST, VEHICLE_WAITING
        )  # going to pick up customer
