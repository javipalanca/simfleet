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
from simfleet.utils.helpers import PathRequestException, distance_in_meters, AlreadyInDestination
from simfleet.communications.protocol import (
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REQUEST_PROTOCOL,
    INFORM_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    PROPOSE_PERFORMATIVE,
    QUERY_PROTOCOL,
    REFUSE_PERFORMATIVE,
)
#from simfleet.common.agents.transport import TransportStrategyBehaviour        #transport.py

from simfleet.common.transportmodels.taxi import TaxiStrategyBehaviour

from simfleet.utils.utils_old import (
    TRANSPORT_WAITING,
    TRANSPORT_WAITING_FOR_APPROVAL,
    TRANSPORT_MOVING_TO_CUSTOMER,
    TRANSPORT_ARRIVED_AT_CUSTOMER,
    TRANSPORT_MOVING_TO_DESTINATION,
    TRANSPORT_ARRIVED_AT_DESTINATION,
    TRANSPORT_IN_CUSTOMER_PLACE,
    TRANSPORT_NEEDS_CHARGING,
    TRANSPORT_MOVING_TO_STATION,
    TRANSPORT_IN_STATION_PLACE,
    TRANSPORT_CHARGING,
    TRANSPORT_CHARGED,
    CUSTOMER_WAITING,
    CUSTOMER_ASSIGNED,
    CUSTOMER_IN_TRANSPORT,
    CUSTOMER_LOCATION,
    CUSTOMER_IN_DEST,
    VEHICLE_WAITING,
    VEHICLE_MOVING_TO_DESTINATION,
    VEHICLE_IN_DEST,
    status_to_str,
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
#                     Transport Strategy                       #
#                                                              #
################################################################
#class TransportWaitingState(TransportStrategyBehaviour, State):
class TaxiWaitingState(TaxiStrategyBehaviour, State):
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_WAITING
        logger.debug("{} in Transport Waiting State".format(self.agent.jid))

    async def run(self):
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_WAITING)
            return
        logger.debug("Transport {} received: {}".format(self.agent.jid, msg.body))
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")
        if performative == REQUEST_PERFORMATIVE:
            if not self.has_enough_autonomy(content["origin"], content["dest"]):
                await self.cancel_proposal(content["customer_id"])
                self.set_next_state(TRANSPORT_NEEDS_CHARGING)
                return
            else:
                await self.send_proposal(content["customer_id"], {})
                self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
                return
        else:
            self.set_next_state(TRANSPORT_WAITING)
            return


#class TransportNeedsChargingState(TransportStrategyBehaviour, State):
class TaxiNeedsChargingState(TaxiStrategyBehaviour, State):
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_NEEDS_CHARGING
        logger.debug("{} in Transport Needs Charging State".format(self.agent.jid))

    async def run(self):
        if (
            self.agent.stations is None
            or len(self.agent.stations) < 1
            and not self.get(name="stations_requested")
        ):
            logger.info("Transport {} looking for a station.".format(self.agent.name))
            self.set(name="stations_requested", value=True)
            await self.send_get_stations()

            msg = await self.receive(timeout=600)
            if not msg:
                self.set_next_state(TRANSPORT_NEEDS_CHARGING)
                return
            logger.debug("Transport received message: {}".format(msg))
            try:
                content = json.loads(msg.body)
            except TypeError:
                content = {}

            performative = msg.get_metadata("performative")
            protocol = msg.get_metadata("protocol")

            if protocol == QUERY_PROTOCOL:
                if performative == INFORM_PERFORMATIVE:
                    self.agent.stations = content
                    logger.info(
                        "Transport {} got list of current stations: {}".format(
                            self.agent.name, len(list(self.agent.stations.keys()))
                        )
                    )
                elif performative == CANCEL_PERFORMATIVE:
                    logger.info(
                        "Transport {} got a cancellation of request for stations information.".format(
                            self.agent.name
                        )
                    )
                    self.set(name="stations_requested", value=False)
                    self.set_next_state(TRANSPORT_NEEDS_CHARGING)
                    return
            else:
                self.set_next_state(TRANSPORT_NEEDS_CHARGING)
                return

        station_positions = []
        for key in self.agent.stations.keys():
            dic = self.agent.stations.get(key)
            station_positions.append((dic["jid"], dic["position"]))
        closest_station = min(
            station_positions,
            key=lambda x: distance_in_meters(x[1], self.agent.get_position()),
        )
        logger.debug("Closest station {}".format(closest_station))
        station = closest_station[0]
        self.agent.current_station_dest = (
            station,
            self.agent.stations[station]["position"],
        )
        logger.info(
            "Transport {} selected station {}.".format(self.agent.name, station)
        )
        try:
            station, position = self.agent.current_station_dest
            await self.go_to_the_station(station, position)
            self.set_next_state(TRANSPORT_MOVING_TO_STATION)
            return
        except PathRequestException:
            logger.error(
                "Transport {} could not get a path to station {}. Cancelling...".format(
                    self.agent.name, station
                )
            )
            await self.cancel_proposal(station)
            self.set_next_state(TRANSPORT_WAITING)
            return
        except Exception as e:
            logger.error(
                "Unexpected error in transport {}: {}".format(self.agent.name, e)
            )
            self.set_next_state(TRANSPORT_WAITING)
            return


#class TransportMovingToStationState(TransportStrategyBehaviour, State):
class TaxiMovingToStationState(TaxiStrategyBehaviour, State):
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_STATION
        logger.debug("{} in Transport Moving to Station".format(self.agent.jid))

    async def run(self):
        if self.agent.get("in_station_place"):
            logger.warning(
                "Transport {} already in station place".format(self.agent.jid)
            )
            await self.agent.request_access_station()
            return self.set_next_state(TRANSPORT_IN_STATION_PLACE)
        self.agent.transport_in_station_place_event.clear()  # new
        self.agent.watch_value(
            "in_station_place", self.agent.transport_in_station_place_callback
        )
        await self.agent.transport_in_station_place_event.wait()
        await self.agent.request_access_station()  # new
        return self.set_next_state(TRANSPORT_IN_STATION_PLACE)


#class TransportInStationState(TransportStrategyBehaviour, State):
class TaxiInStationState(TaxiStrategyBehaviour, State):
    # car arrives to the station and waits in queue until receiving confirmation
    async def on_start(self):
        await super().on_start()
        logger.debug("{} in Transport In Station Place State".format(self.agent.jid))
        self.agent.status = TRANSPORT_IN_STATION_PLACE

    async def run(self):
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_IN_STATION_PLACE)
            return
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")
        if performative == ACCEPT_PERFORMATIVE:
            if content.get("station_id") is not None:
                logger.debug(
                    "Transport {} received a message with ACCEPT_PERFORMATIVE from {}".format(
                        self.agent.name, content["station_id"]
                    )
                )
                await self.charge_allowed()
                self.set_next_state(TRANSPORT_CHARGING)
                return

        else:
            # if the message I receive is not an ACCEPT, I keep waiting in the queue
            self.set_next_state(TRANSPORT_IN_STATION_PLACE)
            return


#class TransportChargingState(TransportStrategyBehaviour, State):
class TaxiChargingState(TaxiStrategyBehaviour, State):
    # car charges in a station
    async def on_start(self):
        await super().on_start()
        logger.debug("{} in Transport Charging State".format(self.agent.jid))

    async def run(self):
        # await "transport_charged" message
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_CHARGING)
            return
        content = json.loads(msg.body)
        protocol = msg.get_metadata("protocol")
        performative = msg.get_metadata("performative")
        if protocol == REQUEST_PROTOCOL and performative == INFORM_PERFORMATIVE:
            if content["status"] == TRANSPORT_CHARGED:
                self.agent.transport_charged()
                await self.agent.drop_station()
                # canviar per un event?
                self.set_next_state(TRANSPORT_WAITING)
                return
        else:
            self.set_next_state(TRANSPORT_CHARGING)
            return


#class TransportWaitingForApprovalState(TransportStrategyBehaviour, State):
class TaxiWaitingForApprovalState(TaxiStrategyBehaviour, State):
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_WAITING_FOR_APPROVAL
        logger.debug(
            "{} in Transport Waiting For Approval State".format(self.agent.jid)
        )

    async def run(self):
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
            return
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")
        if performative == ACCEPT_PERFORMATIVE:
            try:
                logger.debug(
                    "Transport {} got accept from {}".format(
                        self.agent.name, content["customer_id"]
                    )
                )
                # new version
                #self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER
                if not self.check_and_decrease_autonomy(
                    content["origin"], content["dest"]
                ):
                    await self.cancel_proposal(content["customer_id"])
                    self.set_next_state(TRANSPORT_NEEDS_CHARGING)
                    return
                else:
                    # MOD-STRATEGY-01 - comments
                    #await self.pick_up_customer(
                    #    content["customer_id"], content["origin"], content["dest"]
                    #)

                    #1) Send message to customer
                    await self.agent.inform_customer(
                        customer_id=content["customer_id"], status=TRANSPORT_MOVING_TO_CUSTOMER
                    )
                    #2) Save customer assigned data locally
                    # MOD-STRATEGY-01 - new funtion
                    await self.agent.add_customer_in_transport(
                        customer_id=content["customer_id"], in_transport=False,
                        origin=content["origin"], dest=content["dest"]
                    )

                    #3) Initiate movement towards the client
                    await self.agent.move_to(content["origin"])

                    self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER
                    self.set_next_state(TRANSPORT_MOVING_TO_CUSTOMER)
                    return
            except PathRequestException:
                logger.error(
                    "Transport {} could not get a path to customer {}. Cancelling...".format(
                        self.agent.name, content["customer_id"]
                    )
                )
                await self.cancel_proposal(content["customer_id"])
                self.set_next_state(TRANSPORT_WAITING)
                return

            except AlreadyInDestination:
                # 2) Save customer assigned data locally
                # MOD-STRATEGY-01 - new funtion
                await self.agent.inform_customer(
                    customer_id=content["customer_id"], status=TRANSPORT_IN_CUSTOMER_PLACE
                )
                self.agent.status = TRANSPORT_ARRIVED_AT_CUSTOMER
                self.set_next_state(TRANSPORT_ARRIVED_AT_CUSTOMER)
                return
            except Exception as e:
                logger.error(
                    "Unexpected error in transport {}: {}".format(self.agent.name, e)
                )
                await self.cancel_proposal(content["customer_id"])
                self.set_next_state(TRANSPORT_WAITING)
                return

        elif performative == REFUSE_PERFORMATIVE:
            logger.debug(
                "Transport {} got refusal from customer/station".format(self.agent.name)
            )
            self.set_next_state(TRANSPORT_WAITING)
            return

        else:
            self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
            return


#class TransportMovingToCustomerState(TransportStrategyBehaviour, State):
# MOD-STRATEGY-02 - comments
#class TaxiMovingToCustomerState(TaxiStrategyBehaviour, State):
#    async def on_start(self):
#        await super().on_start()
#        self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER
#        logger.debug("{} in Transport Moving To Customer State".format(self.agent.jid))

#    async def run(self):
        # Reset internal flag to False. coroutines calling
        # wait() will block until set() is called
#        self.agent.customer_in_transport_event.clear()
#        # Registers an observer callback to be run when the "customer_in_transport" is changed
#        self.agent.watch_value(
#            "customer_in_transport", self.agent.customer_in_transport_callback
#        )
        # block behaviour until another coroutine calls set()
#        await self.agent.customer_in_transport_event.wait()
#        return self.set_next_state(TRANSPORT_WAITING)

# MOD-STRATEGY-02 - New status
class TaxiMovingToCustomerState(TaxiStrategyBehaviour, State):
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER
        logger.debug("{} in Transport Moving To Customer State".format(self.agent.jid))

    async def run(self):

        customers = self.get("current_customer")
        customer_id = next(iter(customers.items()))[0]

        msg = await self.receive(timeout=2)  # Test 2 seconds

        if msg:

            performative = msg.get_metadata("performative")
            if performative == REQUEST_PERFORMATIVE:
                self.set_next_state(TRANSPORT_MOVING_TO_CUSTOMER)
                return
            elif performative == REFUSE_PERFORMATIVE:
                logger.debug(
                    "Transport {} got refusal from customer/station".format(self.agent.name)
                )
                self.agent.status = TRANSPORT_WAITING
                self.set_next_state(TRANSPORT_WAITING)
                return
        else:

            try:

                if not self.agent.is_in_destination():
                    # await asyncio.sleep(1)
                    self.set_next_state(TRANSPORT_MOVING_TO_CUSTOMER)
                else:
                    logger.info(
                        "Transport {} has arrived to destination. Status: {}".format(
                            self.agent.agent_id, self.agent.status
                        )
                    )
                    await self.agent.inform_customer(
                        customer_id=customer_id, status=TRANSPORT_IN_CUSTOMER_PLACE
                    )
                    self.agent.status = TRANSPORT_ARRIVED_AT_CUSTOMER
                    self.set_next_state(TRANSPORT_ARRIVED_AT_CUSTOMER)
                    return

            except PathRequestException:
                logger.error(
                    "Transport {} could not get a path to customer {}. Cancelling...".format(
                        self.agent.name, customer_id
                    )
                )
                await self.cancel_proposal(customer_id)
                self.agent.status = TRANSPORT_WAITING
                self.set_next_state(TRANSPORT_WAITING)
                return
            except AlreadyInDestination:

                await self.agent.inform_customer(
                    customer_id=customer_id, status=TRANSPORT_IN_CUSTOMER_PLACE
                )
                self.agent.status = TRANSPORT_ARRIVED_AT_CUSTOMER
                self.set_next_state(TRANSPORT_ARRIVED_AT_CUSTOMER)
                return
            except Exception as e:
                logger.error(
                    "Unexpected error in transport {}: {}".format(self.agent.name, e)
                )
                await self.cancel_proposal(customer_id)
                self.agent.status = TRANSPORT_WAITING
                self.set_next_state(TRANSPORT_WAITING)
                return

# MOD-STRATEGY-03 - New status
class TaxiArrivedAtCustomerState(TaxiStrategyBehaviour, State):
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_ARRIVED_AT_CUSTOMER
        logger.debug("{} in Transport Arrived At Customer State".format(self.agent.jid))

    async def run(self):

        customers = self.get("current_customer")
        customer_id = next(iter(customers.items()))[0]

        msg = await self.receive(timeout=60)

        if not msg:
            self.set_next_state(TRANSPORT_ARRIVED_AT_CUSTOMER)
            return
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")

        if performative == INFORM_PERFORMATIVE:
            if "status" in content:
                status = content["status"]

                if status == CUSTOMER_IN_TRANSPORT:

                    try:
                        logger.debug(
                            "Customer {} in transport.".format(self.agent.name)
                        )
                        dest = next(iter(customers.items()))[1]["destination"]

                        await self.agent.add_customer_in_transport(
                            customer_id=customer_id, in_transport=True,
                            dest=dest
                        )

                        logger.info(
                            "Transport {} on route to customer destination of {}".format(self.agent.name, customer_id)
                        )

                        await self.agent.move_to(dest)

                        self.agent.status = TRANSPORT_MOVING_TO_DESTINATION
                        self.set_next_state(TRANSPORT_MOVING_TO_DESTINATION)

                    except PathRequestException:
                        # MOD-STRATEGY-03 - Modify function
                        await self.agent.cancel_customer(customer_id=customer_id)
                        self.agent.status = TRANSPORT_WAITING
                        self.set_next_state(TRANSPORT_WAITING)
                    except AlreadyInDestination:
                        self.set_next_state(TRANSPORT_ARRIVED_AT_DESTINATION)

                    except Exception as e:
                        logger.error(
                            "Unexpected error in transport {}: {}".format(self.agent.name, e)
                        )

        elif performative == CANCEL_PERFORMATIVE:
            self.agent.status = TRANSPORT_WAITING
            self.set_next_state(TRANSPORT_WAITING)
            return
        else:
            self.agent.status = TRANSPORT_ARRIVED_AT_CUSTOMER
            self.set_next_state(TRANSPORT_ARRIVED_AT_CUSTOMER)
            return

#class FSMTransportStrategyBehaviour(FSMBehaviour):
class FSMTaxiStrategyBehaviour(FSMBehaviour):
    def setup(self):
        # Create states
        #self.add_state(TRANSPORT_WAITING, TransportWaitingState(), initial=True)
        self.add_state(TRANSPORT_WAITING, TaxiWaitingState(), initial=True)
        #self.add_state(TRANSPORT_NEEDS_CHARGING, TransportNeedsChargingState())
        self.add_state(TRANSPORT_NEEDS_CHARGING, TaxiNeedsChargingState())
        self.add_state(
            #TRANSPORT_WAITING_FOR_APPROVAL, TransportWaitingForApprovalState()
            TRANSPORT_WAITING_FOR_APPROVAL, TaxiWaitingForApprovalState()
        )

        #self.add_state(TRANSPORT_MOVING_TO_CUSTOMER, TransportMovingToCustomerState())
        self.add_state(TRANSPORT_MOVING_TO_CUSTOMER, TaxiMovingToCustomerState())

        self.add_state(TRANSPORT_ARRIVED_AT_CUSTOMER, TaxiArrivedAtCustomerState())

        #self.add_state(TRANSPORT_MOVING_TO_STATION, TransportMovingToStationState())
        self.add_state(TRANSPORT_MOVING_TO_STATION, TaxiMovingToStationState())
        #self.add_state(TRANSPORT_IN_STATION_PLACE, TransportInStationState())
        self.add_state(TRANSPORT_IN_STATION_PLACE, TaxiInStationState())
        #self.add_state(TRANSPORT_CHARGING, TransportChargingState())
        self.add_state(TRANSPORT_CHARGING, TaxiChargingState())

        # Create transitions
        self.add_transition(
            TRANSPORT_WAITING, TRANSPORT_WAITING
        )  # waiting for messages
        self.add_transition(
            TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL
        )  # accepted by customer
        self.add_transition(
            TRANSPORT_WAITING, TRANSPORT_NEEDS_CHARGING
        )  # not enough charge

        self.add_transition(
            TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_WAITING_FOR_APPROVAL
        )  # waiting for approval message
        self.add_transition(
            TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_WAITING
        )  # transport refused
        self.add_transition(
            TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_MOVING_TO_CUSTOMER
        )  # going to pick up customer

        self.add_transition(
            TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_ARRIVED_AT_CUSTOMER
        )  # going to pick up customer

        self.add_transition(
            TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_MOVING_TO_CUSTOMER
        )  # going to pick up customer

        self.add_transition(
            TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_WAITING
        )  # going to pick up customer

        self.add_transition(
            TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_ARRIVED_AT_CUSTOMER
        )

        self.add_transition(
            TRANSPORT_ARRIVED_AT_CUSTOMER, TRANSPORT_ARRIVED_AT_CUSTOMER
        )  # going to pick up customer

        self.add_transition(
            TRANSPORT_ARRIVED_AT_CUSTOMER, TRANSPORT_MOVING_TO_DESTINATION
        )  # going to pick up customer

        self.add_transition(
            TRANSPORT_ARRIVED_AT_CUSTOMER, TRANSPORT_ARRIVED_AT_DESTINATION
        )  # going to pick up customer

        self.add_transition(
            TRANSPORT_ARRIVED_AT_CUSTOMER, TRANSPORT_WAITING
        )  # going to pick up customer

        self.add_transition(
            TRANSPORT_NEEDS_CHARGING, TRANSPORT_NEEDS_CHARGING
        )  # waiting for station list
        self.add_transition(
            TRANSPORT_NEEDS_CHARGING, TRANSPORT_MOVING_TO_STATION
        )  # going to station
        self.add_transition(
            TRANSPORT_NEEDS_CHARGING, TRANSPORT_WAITING
        )  # exception in go_to_the_station(station, position)
        self.add_transition(
            TRANSPORT_MOVING_TO_STATION, TRANSPORT_IN_STATION_PLACE
        )  # arrived to station
        self.add_transition(
            TRANSPORT_IN_STATION_PLACE, TRANSPORT_IN_STATION_PLACE
        )  # waiting in station queue
        self.add_transition(
            TRANSPORT_IN_STATION_PLACE, TRANSPORT_CHARGING
        )  # begin charging
        self.add_transition(
            TRANSPORT_CHARGING, TRANSPORT_CHARGING
        )  # waiting to finish charging
        self.add_transition(TRANSPORT_CHARGING, TRANSPORT_WAITING)  # restart strategy

        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_MOVING_TO_CUSTOMER)
        self.add_transition(
            TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_WAITING
        )  # picked up customer or arrived to destination ??


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
                        elif status == CUSTOMER_IN_DEST:
                            self.agent.status = CUSTOMER_IN_DEST
                            self.agent.end_time = time.time()
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
