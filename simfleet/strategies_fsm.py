import asyncio
import json
import time
from asyncio import CancelledError

from loguru import logger
from spade.behaviour import State, FSMBehaviour

#from simfleet.common.agents.customer import CustomerStrategyBehaviour
from simfleet.common.customermodels.taxicustomer import TaxiCustomerStrategyBehaviour
from simfleet.common.agents.fleetmanager import FleetManagerStrategyBehaviour
from simfleet.common.vehicle import VehicleStrategyBehaviour    #New vehicle
from simfleet.utils.helpers import PathRequestException, AlreadyInDestination
from simfleet.communications.protocol import (
    INFORM_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    PROPOSE_PERFORMATIVE,
    QUERY_PROTOCOL,
)
#from simfleet.common.agents.transport import TransportStrategyBehaviour        #transport.py

from simfleet.utils.utils_old import (
    TRANSPORT_MOVING_TO_CUSTOMER,
    TRANSPORT_IN_CUSTOMER_PLACE,
    CUSTOMER_WAITING,
    CUSTOMER_ASSIGNED,
    CUSTOMER_IN_TRANSPORT,
    CUSTOMER_IN_DEST,
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
#                       Customer Strategy                      #
#                                                              #
################################################################
#class AcceptFirstRequestBehaviour(CustomerStrategyBehaviour):
class AcceptFirstRequestBehaviour(TaxiCustomerStrategyBehaviour):
    """
    The default strategy for the Customer agent. By default it accepts the first proposal it receives.
    """

    async def run(self):
        if self.agent.fleetmanagers is None:
            await self.send_get_managers(self.agent.fleet_type)

            msg = await self.receive(timeout=300)
            if msg:
                protocol = msg.get_metadata("protocol")
                if protocol == QUERY_PROTOCOL:
                    performative = msg.get_metadata("performative")
                    if performative == INFORM_PERFORMATIVE:
                        self.agent.fleetmanagers = json.loads(msg.body)
                        logger.info(
                            "{} got fleet managers {}".format(
                                self.agent.name, self.agent.fleetmanagers
                            )
                        )
                    elif performative == CANCEL_PERFORMATIVE:
                        logger.info(
                            "{} got cancellation of request for {} information".format(
                                self.agent.name, self.agent.fleet_type
                            )
                        )
            return

        if self.agent.status == CUSTOMER_WAITING:
            await self.send_request(content={})

        try:
            msg = await self.receive(timeout=5)

            if msg:
                performative = msg.get_metadata("performative")
                transport_id = msg.sender
                content = json.loads(msg.body)
                logger.debug("Customer {} informed of: {}".format(self.agent.name, content))

                if performative == PROPOSE_PERFORMATIVE:
                    if self.agent.status == CUSTOMER_WAITING:
                        logger.debug(
                            "Customer {} received proposal from transport {}".format(
                                self.agent.name, transport_id
                            )
                        )
                        await self.accept_transport(transport_id)
                        self.agent.status = CUSTOMER_ASSIGNED
                    else:
                        await self.refuse_transport(transport_id)

                elif performative == CANCEL_PERFORMATIVE:
                    if self.agent.transport_assigned == str(transport_id):
                        logger.warning(
                            "Customer {} received a CANCEL from Transport {}.".format(
                                self.agent.name, transport_id
                            )
                        )
                        self.agent.status = CUSTOMER_WAITING

                elif performative == INFORM_PERFORMATIVE:
                    if "status" in content:
                        status = content["status"]
                        # if status != CUSTOMER_LOCATION:
                        #    logger.debug(
                        #        "Customer {} informed of status: {}".format(
                        #            self.agent.name, status_to_str(status)
                        #        )
                        #    )
                        if status == TRANSPORT_MOVING_TO_CUSTOMER:
                            logger.info(
                                "Customer {} waiting for transport.".format(self.agent.name)
                            )
                            self.agent.waiting_for_pickup_time = time.time()
                        elif status == TRANSPORT_IN_CUSTOMER_PLACE:
                            self.agent.status = CUSTOMER_IN_TRANSPORT
                            logger.info("Customer {} in transport.".format(self.agent.name))
                            self.agent.pickup_time = time.time()
                            await self.inform_transport(transport_id, CUSTOMER_IN_TRANSPORT)
                        elif status == CUSTOMER_IN_DEST:
                            self.agent.status = CUSTOMER_IN_DEST
                            self.agent.end_time = time.time()
                            await self.inform_transport(transport_id, CUSTOMER_IN_DEST)
                            logger.info(
                                "Customer {} arrived to destination after {} seconds.".format(
                                    self.agent.name, self.agent.total_time()
                                )
                            )
        #TravelBehaviour - customer.py
        # try:
            # msg = await self.receive(timeout=5)
            # if not msg:
            #    return
            # content = json.loads(msg.body)
            # logger.debug("Customer {} informed of: {}".format(self.agent.name, content))
            # if "status" in content:
            #    status = content["status"]
            #    if status != CUSTOMER_LOCATION:
            #        logger.debug(
            #            "Customer {} informed of status: {}".format(
            #                self.agent.name, status_to_str(status)
            #            )
            #        )
            #    if status == TRANSPORT_MOVING_TO_CUSTOMER:
            #        logger.info(
            #            "Customer {} waiting for transport.".format(self.agent.name)
            #        )
            #        self.agent.waiting_for_pickup_time = time.time()
            #    elif status == TRANSPORT_IN_CUSTOMER_PLACE:
            #        self.agent.status = CUSTOMER_IN_TRANSPORT
            #        logger.info("Customer {} in transport.".format(self.agent.name))
            #        self.agent.pickup_time = time.time()
            #    elif status == CUSTOMER_IN_DEST:
            #        self.agent.status = CUSTOMER_IN_DEST
            #        self.agent.end_time = time.time()
            #        logger.info(
            #            "Customer {} arrived to destination after {} seconds.".format(
            #                self.agent.name, self.agent.total_time()
            #            )
            #        )
            # elif status == CUSTOMER_LOCATION:
            #    coords = content["location"]
            #    self.agent.set_position(coords)
        except CancelledError:
            logger.debug("Cancelling async tasks...")

        except Exception as e:
            logger.error(
                "EXCEPTION in AcceptFirstRequestBehaviour of Customer {}: {}".format(
                    self.agent.name, e
                )
            )



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
