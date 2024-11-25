import json
import asyncio

from loguru import logger
from simfleet.utils.abstractstrategies import FSMSimfleetBehaviour

from simfleet.common.lib.transports.models.electrictaxi import ElectricTaxiStrategyBehaviour
from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    REQUEST_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE
)

from simfleet.utils.helpers import (
    PathRequestException,
    AlreadyInDestination
)
from simfleet.utils.status import TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_MOVING_TO_CUSTOMER, \
    TRANSPORT_ARRIVED_AT_CUSTOMER, TRANSPORT_IN_CUSTOMER_PLACE, TRANSPORT_MOVING_TO_DESTINATION, \
    TRANSPORT_ARRIVED_AT_DESTINATION, TRANSPORT_MOVING_TO_STATION, TRANSPORT_IN_STATION_PLACE, \
    TRANSPORT_IN_WAITING_LIST, TRANSPORT_NEEDS_CHARGING, TRANSPORT_CHARGING, CUSTOMER_IN_TRANSPORT, CUSTOMER_IN_DEST


################################################################
#                                                              #
#                    Electric Taxi Strategy                    #
#                                                              #
################################################################

class ElectricTaxiWaitingState(ElectricTaxiStrategyBehaviour):
    """
        Represents the 'Waiting' state for the electric taxi. The taxi is waiting to receive a transport request.

        Methods:
            on_start(): Sets the initial state to 'TRANSPORT_WAITING' and logs the state.
            run(): Handles incoming messages, processes transport requests, and transitions to the next state.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_WAITING
        #logger.debug("{} in Transport Waiting State".format(self.agent.jid))

    async def run(self):
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_WAITING)
            return
        logger.debug("Agent[{}]: The agent received: {}".format(self.agent.jid, msg.body))
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")
        if performative == REQUEST_PERFORMATIVE:

            # New statistics
            # Event 1: Customer Request Reception
            self.agent.events_store.emit(
                event_type="customer_request_reception",
                details={}
            )

            if not self.agent.has_enough_autonomy(content["origin"], content["dest"]):

                # New statistics
                # Event 1e: Need for Service
                self.agent.events_store.emit(
                    event_type="transport_need_for_service",
                    details={}
                )

                await self.cancel_proposal(content["customer_id"])
                self.set_next_state(TRANSPORT_NEEDS_CHARGING)
                return
            else:

                # New statistics
                # Event 2: Transport Offer
                self.agent.events_store.emit(
                    event_type="transport_offer",
                    details={}
                )

                await self.send_proposal(content["customer_id"], {})
                self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
                return
        else:
            self.set_next_state(TRANSPORT_WAITING)
            return

class ElectricTaxiNeedsChargingState(ElectricTaxiStrategyBehaviour):
    """
        Represents the 'Needs Charging' state. The taxi is searching for or moving to a charging station.

        Methods:
            on_start(): Logs the transition to the 'Needs Charging' state.
            run(): Manages the behavior of the taxi while it finds a charging station and handles exceptions.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_NEEDS_CHARGING
        #logger.debug("{} in Transport Needs Charging State".format(self.agent.jid))

    async def run(self):

        if (
            self.agent.get_stations() is None
            or self.agent.get_number_stations() < 1
        ):
            logger.info("Agent[{}]: The agent looking for a station.".format(self.agent.name))

            # New
            stations = await self.agent.get_list_agent_position(self.agent.service_type, self.agent.get_stations())

            self.agent.set_stations(stations)

            self.set_next_state(TRANSPORT_NEEDS_CHARGING)
            return

        else:

            nearby_station_dest = self.agent.nearst_agent(self.agent.get_stations(), self.agent.get_position())

            self.agent.set_nearby_station(nearby_station_dest)

            logger.info(
                 "Agent[{}]: The agent selected station [{}].".format(self.agent.name, self.agent.get_nearby_station_id())
             )

            try:

                await self.go_to_the_station(self.agent.get_nearby_station_id(), self.agent.get_nearby_station_position())

                # New statistics - TESTING
                path, distance, duration = await self.agent.request_path(
                    self.agent.get("current_pos"), self.agent.get_nearby_station_position()
                )

                # New statistics
                # Event 2e: Travel to Station
                self.agent.events_store.emit(
                    event_type="travel_to_station",
                    details={"distance": distance}
                )

                try:
                    logger.debug("{} move_to station {}".format(self.agent.name, self.agent.get_nearby_station_id()))
                    await self.agent.move_to(self.agent.get_nearby_station_position())

                    self.agent.status = TRANSPORT_MOVING_TO_STATION
                    self.set_next_state(TRANSPORT_MOVING_TO_STATION)

                except AlreadyInDestination:
                    logger.debug(
                        "Agent[{}]: The agent is already in the stations' ({}) position. . .".format(
                            self.agent.name, self.agent.get_nearby_station_id()
                        )
                    )

                    self.agent.arguments["transport_need"] = self.agent.max_autonomy_km - self.agent.current_autonomy_km

                    content = {"service_name": self.agent.service_type,
                            "args": self.agent.arguments}
                    await self.request_access_station(self.agent.get("current_station"), content)

                    self.agent.status = TRANSPORT_IN_STATION_PLACE
                    self.set_next_state(TRANSPORT_IN_STATION_PLACE)
                    return

                return

            except PathRequestException:
                logger.error(
                    "Agent[{}]: The agent could not get a path to station [{}]. Cancelling...".format(
                        self.agent.name, self.agent.get_nearby_station_id()
                    )
                )
                await self.cancel_proposal(self.agent.get_nearby_station_id())
                self.agent.status = TRANSPORT_WAITING
                self.set_next_state(TRANSPORT_WAITING)
                return
            except Exception as e:
                logger.error(
                    "Unexpected error in transport [{}]: {}".format(self.agent.name, e)
                )
                self.agent.status = TRANSPORT_WAITING
                self.set_next_state(TRANSPORT_WAITING)
                return


class ElectricTaxiMovingToStationState(ElectricTaxiStrategyBehaviour):
    """
        Represents the state where the taxi is moving towards the charging station.

        Methods:
            on_start(): Logs the transition to 'Moving to Station'.
            run(): Handles movement towards the charging station and transitions accordingly.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_STATION
        #logger.debug("{} in Transport Moving to Station".format(self.agent.jid))

    async def run(self):
        try:

            if not self.agent.is_in_destination():

                await self.agent.sleep(1)
                self.set_next_state(TRANSPORT_MOVING_TO_STATION)
            else:

                self.agent.arguments["transport_need"] = self.agent.max_autonomy_km - self.agent.current_autonomy_km

                # New statistics
                # Event 3e: Arrival at Station
                self.agent.events_store.emit(
                    event_type="arrival_at_station",
                    details={}
                )

                content = {"service_name": self.agent.service_type, "object_type": "transport", "args": self.agent.arguments}
                await self.request_access_station(self.agent.get("current_station"), content)

                self.agent.status = TRANSPORT_IN_STATION_PLACE
                self.set_next_state(TRANSPORT_IN_STATION_PLACE)

        except AlreadyInDestination:
            logger.warning(
                "Agent[{}]: The agent has arrived to destination.".format(
                    self.agent.agent_id
                )
            )

            self.agent.arguments["transport_need"] = self.agent.max_autonomy_km - self.agent.current_autonomy_km

            content = {"service_name": self.agent.service_type, "args": self.agent.arguments}
            await self.request_access_station(self.agent.get("current_station"), content)

            # New statistics
            # Event 3e: Arrival at Station
            self.agent.events_store.emit(
                event_type="arrival_at_station",
                details={}
            )

            self.agent.status = TRANSPORT_IN_STATION_PLACE
            self.set_next_state(TRANSPORT_IN_STATION_PLACE)
            return
        except PathRequestException:
            logger.error(
                "Agent[{}]: The agent could not get a path to customer. Cancelling...".format(
                    self.agent.name
                )
            )
            self.agent.status = TRANSPORT_WAITING
            self.set_next_state(TRANSPORT_WAITING)
            return


class ElectricTaxiInStationState(ElectricTaxiStrategyBehaviour):
    """
        Represents the state where the taxi is at the charging station, waiting for confirmation to begin charging.

        Methods:
            on_start(): Logs the transition to 'In Station Place'.
            run(): Handles the taxi's behavior while waiting in the station queue.
        """
    async def on_start(self):
        await super().on_start()
        #logger.debug("{} in Transport In Station Place State".format(self.agent.jid))
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
                    "Agent[{}]: The agent received a message with ACCEPT_PERFORMATIVE from [{}]".format(
                        self.agent.name, content["station_id"]
                    )
                )

                # New statistics
                # Event 4e: Wait for Service
                self.agent.events_store.emit(
                    event_type="wait_for_service",
                    details={}
                )

                self.agent.status = TRANSPORT_IN_WAITING_LIST
                self.set_next_state(TRANSPORT_IN_WAITING_LIST)

                return

        elif performative == REFUSE_PERFORMATIVE:
            self.agent.status = TRANSPORT_NEEDS_CHARGING
            self.set_next_state(TRANSPORT_NEEDS_CHARGING)
            return

        else:

            self.set_next_state(TRANSPORT_IN_STATION_PLACE)
            return


class ElectricTaxiInWaitingListState(ElectricTaxiStrategyBehaviour):
    """
        Represents the state where the taxi is in the waiting list at the charging station.

        Methods:
            on_start(): Logs the transition to 'In Waiting List'.
            run(): Handles waiting for confirmation to start charging.
        """
    async def on_start(self):
        await super().on_start()
        #logger.debug("{} in Transport In Station Place State".format(self.agent.jid))
        self.agent.status = TRANSPORT_IN_WAITING_LIST

    async def run(self):

        msg = await self.receive(timeout=5)
        if not msg:
            self.set_next_state(TRANSPORT_IN_WAITING_LIST)
            return
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")

        if performative == INFORM_PERFORMATIVE:
            if content.get("station_id") is not None:
                logger.debug(
                    "Agent[{}]: The agent received a message with INFORM_PERFORMATIVE from [{}]".format(
                        self.agent.name, content["station_id"]
                    )
                )
                if content.get("serving") is not None and content.get("serving"):

                    # New statistics
                    # Event 5e: Service Start
                    self.agent.events_store.emit(
                        event_type="service_start",
                        details={}
                    )

                    self.agent.status = TRANSPORT_CHARGING
                    self.set_next_state(TRANSPORT_CHARGING)
                    return

        elif performative == REFUSE_PERFORMATIVE:
            if content.get("station_id") is not None:
                logger.debug(
                    "Agent[{}]: The agent received a message with REFUSE_PERFORMATIVE from [{}]".format(
                        self.agent.name, content["station_id"]
                    )
                )
                self.agent.status = TRANSPORT_NEEDS_CHARGING
                self.set_next_state(TRANSPORT_NEEDS_CHARGING)

        else:
            self.set_next_state(TRANSPORT_IN_WAITING_LIST)
            return


class ElectricTaxiChargingState(ElectricTaxiStrategyBehaviour):
    """
        Represents the 'Charging' state. The taxi is currently charging in the station.

        Methods:
            on_start(): Logs the transition to 'Charging'.
            run(): Monitors the charging process and transitions back to 'Waiting' when charging completes.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_CHARGING
        #logger.debug("{} in Transport Charging State".format(self.agent.jid))

    async def run(self):

        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_CHARGING)
            return
        content = json.loads(msg.body)
        protocol = msg.get_metadata("protocol")
        performative = msg.get_metadata("performative")
        if protocol == REQUEST_PROTOCOL and performative == INFORM_PERFORMATIVE:
            if content["charged"]:
                self.agent.increase_full_autonomy_km()
                await self.drop_station()

                # New statistics
                # Event 6e: Service Completion
                self.agent.events_store.emit(
                    event_type="service_completion",
                    details={}
                )

                self.agent.status = TRANSPORT_WAITING
                self.set_next_state(TRANSPORT_WAITING)
                return
        else:
            self.set_next_state(TRANSPORT_CHARGING)
            return


class ElectricTaxiWaitingForApprovalState(ElectricTaxiStrategyBehaviour):
    """
        Represents the state where the taxi is waiting for approval from a customer or station.
        After making a transport offer, the taxi waits for a response (approval or refusal).

        Methods:
            on_start(): Logs the transition to 'Waiting For Approval'.
            run(): Handles incoming approval or refusal messages and transitions accordingly.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_WAITING_FOR_APPROVAL
        #logger.debug(
        #    "{} in Transport Waiting For Approval State".format(self.agent.jid)
        #)

    async def run(self):
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
            return
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")
        if performative == ACCEPT_PERFORMATIVE:
            # Handle acceptance by the customer or station
            try:
                logger.debug(
                    "Agent[{}]: The agent got accept from [{}]".format(
                        self.agent.name, content["customer_id"]
                    )
                )
                if not self.check_and_decrease_autonomy(
                    content["origin"], content["dest"]
                ):
                    await self.cancel_proposal(content["customer_id"])
                    self.set_next_state(TRANSPORT_NEEDS_CHARGING)
                    return
                else:

                    # New statistics
                    # Event 3: Transport Offer Acceptance
                    self.agent.events_store.emit(
                        event_type="transport_offer_acceptance",
                        details={}
                    )

                    await self.agent.inform_customer(
                        customer_id=content["customer_id"], status=TRANSPORT_MOVING_TO_CUSTOMER
                    )

                    await self.agent.add_assigned_taxicustomer(
                        customer_id=content["customer_id"],
                        origin=content["origin"], dest=content["dest"]
                    )

                    #New statistics - TESTING
                    path, distance, duration = await self.agent.request_path(
                        self.agent.get("current_pos"), content["origin"]
                    )

                    # New statistics
                    # Event 4: Travel to Pickup
                    self.agent.events_store.emit(
                        event_type="travel_to_pickup",
                        details={"distance": distance, "duration": duration}
                    )

                    await self.agent.move_to(content["origin"])

                    self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER
                    self.set_next_state(TRANSPORT_MOVING_TO_CUSTOMER)
                    return
            except PathRequestException:
                logger.error(
                    "Agent[{}]: The agent could not get a path to customer [{}]. Cancelling...".format(
                        self.agent.name, content["customer_id"]
                    )
                )
                await self.cancel_proposal(content["customer_id"])
                self.set_next_state(TRANSPORT_WAITING)
                return

            except AlreadyInDestination:

                await self.agent.inform_customer(
                    customer_id=content["customer_id"], status=TRANSPORT_IN_CUSTOMER_PLACE
                )
                self.agent.status = TRANSPORT_ARRIVED_AT_CUSTOMER
                self.set_next_state(TRANSPORT_ARRIVED_AT_CUSTOMER)
                return
            except Exception as e:
                logger.error(
                    "Unexpected error in transport [{}]: {}".format(self.agent.name, e)
                )
                await self.cancel_proposal(content["customer_id"])
                self.set_next_state(TRANSPORT_WAITING)
                return

        elif performative == REFUSE_PERFORMATIVE:
            logger.debug(
                "Agent[{}]: The agent got refusal from customer/station".format(self.agent.name)
            )
            self.set_next_state(TRANSPORT_WAITING)
            return

        else:
            self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
            return

class ElectricTaxiMovingToCustomerState(ElectricTaxiStrategyBehaviour):
    """
        Represents the state where the taxi is moving towards the customer to pick them up.

        Methods:
            on_start(): Logs the transition to 'Moving To Customer'.
            run(): Handles the movement to the customer and manages unexpected issues during the trip.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER
        #logger.debug("{} in Transport Moving To Customer State".format(self.agent.jid))

    async def run(self):

        customers = self.get("assigned_customer")
        customer_id = next(iter(customers.items()))[0]

        try:

            if not self.agent.is_in_destination():

                msg = await self.receive(timeout=2)

                if msg:

                    performative = msg.get_metadata("performative")
                    if performative == REQUEST_PERFORMATIVE:
                        self.set_next_state(TRANSPORT_MOVING_TO_CUSTOMER)
                        return
                    elif performative == REFUSE_PERFORMATIVE:
                        logger.debug(
                            "Agent[{}]: The agent got refusal from customer/station".format(self.agent.name)
                        )
                        self.agent.status = TRANSPORT_WAITING
                        self.set_next_state(TRANSPORT_WAITING)
                        return

                else:
                    self.set_next_state(TRANSPORT_MOVING_TO_CUSTOMER)
            else:
                logger.info(
                    "Agent[{}]: The agent has arrived to destination. Status: {}".format(
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
                "Agent[{}]: The agent could not get a path to customer [{}]. Cancelling...".format(
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
                "Unexpected error in transport [{}]: {}".format(self.agent.name, e)
            )
            await self.cancel_proposal(customer_id)
            self.agent.status = TRANSPORT_WAITING
            self.set_next_state(TRANSPORT_WAITING)
            return


class ElectricTaxiArrivedAtCustomerState(ElectricTaxiStrategyBehaviour):
    """
        Represents the state where the taxi has arrived at the customer's location.

        Methods:
            on_start(): Logs the transition to 'Arrived At Customer'.
            run(): Handles the pickup of the customer and begins the journey to their destination.
        """

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_ARRIVED_AT_CUSTOMER
        #logger.debug("{} in Transport Arrived At Customer State".format(self.agent.jid))

    async def run(self):

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

                    customers = self.get("assigned_customer")
                    customer_id = next(iter(customers.items()))[0]
                    dest = next(iter(customers.items()))[1]["destination"]

                    try:
                        logger.debug(
                            "Agent[{}]: Customer [{}] in transport.".format(self.agent.name, customer_id)
                        )

                        self.agent.add_customer_in_transport(
                            customer_id=customer_id, dest=dest
                        )
                        await self.agent.remove_assigned_taxicustomer()

                        logger.info(
                            "Agent[{}]: The agent on route to [{}] destination".format(self.agent.name, customer_id)
                        )

                        # New statistics
                        # Event 5: Customer Pickup
                        self.agent.events_store.emit(
                            event_type="customer_pickup",
                            details={},
                        )

                        # New statistics - TESTING
                        path, distance, duration = await self.agent.request_path(
                            self.agent.get("current_pos"), dest
                        )

                        await self.agent.move_to(dest)

                        # New statistics
                        # Event 6: Travel to destination
                        self.agent.events_store.emit(
                            event_type="travel_to_destination",
                            details={"distance": distance},
                        )

                        self.agent.status = TRANSPORT_MOVING_TO_DESTINATION
                        self.set_next_state(TRANSPORT_MOVING_TO_DESTINATION)

                    except PathRequestException:
                        await self.agent.cancel_customer(customer_id=customer_id)
                        self.agent.status = TRANSPORT_WAITING
                        self.set_next_state(TRANSPORT_WAITING)
                    except AlreadyInDestination:
                        self.set_next_state(TRANSPORT_ARRIVED_AT_DESTINATION)

                    except Exception as e:
                        logger.error(
                            "Unexpected error in transport [{}]: {}".format(self.agent.name, e)
                        )

        elif performative == CANCEL_PERFORMATIVE:
            self.agent.status = TRANSPORT_WAITING
            self.set_next_state(TRANSPORT_WAITING)
            return
        else:
            self.agent.status = TRANSPORT_ARRIVED_AT_CUSTOMER
            self.set_next_state(TRANSPORT_ARRIVED_AT_CUSTOMER)
            return

# MOD-STRATEGY-04 - New status
class ElectricTaxiMovingToCustomerDestState(ElectricTaxiStrategyBehaviour):
    """
        Represents the state where the taxi is transporting the customer to their destination.

        Methods:
            on_start(): Logs the transition to 'Moving To Destination'.
            run(): Manages the trip to the customer's destination.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_DESTINATION
        #logger.debug("{} in Transport Moving To Customer Dest State".format(self.agent.jid))

    async def run(self):

        customers = self.get("current_customer")
        customer_id = next(iter(customers.items()))[0]

        try:

            if not self.agent.is_in_destination():
                await self.agent.sleep(1)
                self.set_next_state(TRANSPORT_MOVING_TO_DESTINATION)
            else:
                logger.info(
                    "Agent[{}]: The agent has arrived to destination. Status: {}".format(
                        self.agent.agent_id, self.agent.status
                    )
                )

                # New statistics
                # Event 6: Trip completion
                self.agent.events_store.emit(
                    event_type="trip_completion",
                    details={},
                )

                await self.agent.inform_customer(
                    customer_id=customer_id, status=CUSTOMER_IN_DEST
                )
                self.agent.status = TRANSPORT_ARRIVED_AT_DESTINATION
                self.set_next_state(TRANSPORT_ARRIVED_AT_DESTINATION)

        except PathRequestException:
            logger.error(
                "Agent[{}]: The agent could not get a path to customer [{}]. Cancelling...".format(
                    self.agent.name, customer_id
                )
            )
            await self.cancel_proposal(customer_id)
            self.agent.status = TRANSPORT_WAITING
            self.set_next_state(TRANSPORT_WAITING)
            return
        except AlreadyInDestination:

            # New statistics
            # Event 6: Trip completion
            self.agent.events_store.emit(
                event_type="trip_completion",
                details={},
            )

            await self.agent.inform_customer(
                customer_id=customer_id, status=CUSTOMER_IN_DEST
            )
            self.agent.status = TRANSPORT_ARRIVED_AT_DESTINATION
            self.set_next_state(TRANSPORT_ARRIVED_AT_DESTINATION)
            return
        except Exception as e:
            logger.error(
                "Unexpected error in transport [{}]: {}".format(self.agent.name, e)
            )
            await self.cancel_proposal(customer_id)
            self.agent.status = TRANSPORT_WAITING
            self.set_next_state(TRANSPORT_WAITING)
            return

class ElectricTaxiArrivedAtCustomerDestState(ElectricTaxiStrategyBehaviour):
    """
        Represents the state where the taxi has arrived at the customer's destination.

        Methods:
            on_start(): Logs the transition to 'Arrived At Destination'.
            run(): Handles the process of dropping the customer off and resets the taxi to 'Waiting' state.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_ARRIVED_AT_DESTINATION
        #logger.debug("{} in Transport Arrived at Customer Dest State".format(self.agent.jid))

    async def run(self):

        customers = self.get("current_customer")
        customer_id = next(iter(customers.items()))[0]

        msg = await self.receive(timeout=60)

        if not msg:
            self.set_next_state(TRANSPORT_ARRIVED_AT_DESTINATION)
            return
        else:
            content = json.loads(msg.body)
            performative = msg.get_metadata("performative")

            if performative == INFORM_PERFORMATIVE:
                if "status" in content:
                    status = content["status"]

                    if status == CUSTOMER_IN_DEST:

                        self.agent.remove_customer_in_transport(customer_id)
                        logger.debug(
                            "Agent[{}]: The agent has dropped the customer [{}] in destination.".format(
                                self.agent.agent_id, customer_id
                            )
                        )
                        self.agent.status = TRANSPORT_WAITING
                        self.set_next_state(TRANSPORT_WAITING)
                        return

            elif performative == CANCEL_PERFORMATIVE:
                self.agent.status = TRANSPORT_WAITING
                self.set_next_state(TRANSPORT_WAITING)
                return
            else:
                self.set_next_state(TRANSPORT_ARRIVED_AT_DESTINATION)
                return


class FSMElectricTaxiBehaviour(FSMSimfleetBehaviour):
    """
    Represents the Finite State Machine (FSM) strategy for the electric taxi agent.
    This class manages the different states and transitions for the taxi based on its behavior,
    including waiting for customers, moving to charging stations, and traveling to destinations.

    Methods:
        setup(): Initializes all states and defines transitions between them.
    """

    def setup(self):
        """
        Sets up the FSM by adding states and defining transitions.
        This method creates the states the electric taxi can be in and
        specifies the valid transitions between these states.
        """

        # Add states to the FSM
        self.add_state(TRANSPORT_WAITING, ElectricTaxiWaitingState(), initial=True)
        self.add_state(TRANSPORT_NEEDS_CHARGING, ElectricTaxiNeedsChargingState())
        self.add_state(TRANSPORT_WAITING_FOR_APPROVAL, ElectricTaxiWaitingForApprovalState())
        self.add_state(TRANSPORT_MOVING_TO_CUSTOMER, ElectricTaxiMovingToCustomerState())
        self.add_state(TRANSPORT_ARRIVED_AT_CUSTOMER, ElectricTaxiArrivedAtCustomerState())
        self.add_state(TRANSPORT_MOVING_TO_DESTINATION, ElectricTaxiMovingToCustomerDestState())
        self.add_state(TRANSPORT_ARRIVED_AT_DESTINATION, ElectricTaxiArrivedAtCustomerDestState())
        self.add_state(TRANSPORT_MOVING_TO_STATION, ElectricTaxiMovingToStationState())
        self.add_state(TRANSPORT_IN_STATION_PLACE, ElectricTaxiInStationState())
        self.add_state(TRANSPORT_IN_WAITING_LIST, ElectricTaxiInWaitingListState())
        self.add_state(TRANSPORT_CHARGING, ElectricTaxiChargingState())

        # Define transitions between states

        # Transitions related to the 'Waiting' state
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_WAITING)  # Remains in waiting if no new action
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL)  # When a customer accepts a proposal
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_NEEDS_CHARGING)  # If the taxi needs charging

        # Transitions from 'Waiting For Approval' state
        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_WAITING_FOR_APPROVAL)  # Keep waiting for approval
        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_WAITING)  # If the proposal is refused
        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_MOVING_TO_CUSTOMER)  # If the customer accepts
        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_ARRIVED_AT_CUSTOMER)  # Direct arrival scenario

        # Transitions from 'Moving To Customer' state
        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_MOVING_TO_CUSTOMER)  # Still moving
        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_WAITING)  # Encounter an issue, go back to waiting
        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_ARRIVED_AT_CUSTOMER)  # Successfully arrive

        # Transitions from 'Arrived At Customer' state
        self.add_transition(TRANSPORT_ARRIVED_AT_CUSTOMER, TRANSPORT_ARRIVED_AT_CUSTOMER)  # Waiting at customer's location
        self.add_transition(TRANSPORT_ARRIVED_AT_CUSTOMER, TRANSPORT_MOVING_TO_DESTINATION)  # Begin journey to destination
        self.add_transition(TRANSPORT_ARRIVED_AT_CUSTOMER, TRANSPORT_ARRIVED_AT_DESTINATION)  # Direct destination arrival
        self.add_transition(TRANSPORT_ARRIVED_AT_CUSTOMER, TRANSPORT_WAITING)  # Cancel and return to waiting

        # Transitions from 'Moving To Destination' state
        self.add_transition(TRANSPORT_MOVING_TO_DESTINATION, TRANSPORT_MOVING_TO_DESTINATION)  # Still moving to destination
        self.add_transition(TRANSPORT_MOVING_TO_DESTINATION, TRANSPORT_WAITING)  # An issue encountered, return to waiting
        self.add_transition(TRANSPORT_MOVING_TO_DESTINATION, TRANSPORT_ARRIVED_AT_DESTINATION)  # Arrival at destination

        # Transitions from 'Arrived At Destination' state
        self.add_transition(TRANSPORT_ARRIVED_AT_DESTINATION, TRANSPORT_ARRIVED_AT_DESTINATION)  # Stay at destination
        self.add_transition(TRANSPORT_ARRIVED_AT_DESTINATION, TRANSPORT_WAITING)  # Drop customer and return to waiting

        # Transitions related to the 'Needs Charging' state
        self.add_transition(TRANSPORT_NEEDS_CHARGING, TRANSPORT_NEEDS_CHARGING)  # Continue searching for a station
        self.add_transition(TRANSPORT_NEEDS_CHARGING, TRANSPORT_WAITING)  # Issue finding station, return to waiting
        self.add_transition(TRANSPORT_NEEDS_CHARGING, TRANSPORT_MOVING_TO_STATION)  # Successfully heading to station
        self.add_transition(TRANSPORT_NEEDS_CHARGING, TRANSPORT_IN_STATION_PLACE)  # Arrives at the station

        # Transitions from 'Moving To Station' state
        self.add_transition(TRANSPORT_MOVING_TO_STATION, TRANSPORT_MOVING_TO_STATION)  # Still heading to the station
        self.add_transition(TRANSPORT_MOVING_TO_STATION, TRANSPORT_IN_STATION_PLACE)  # Arrives at station

        # Transitions from 'In Station Place' state
        self.add_transition(TRANSPORT_IN_STATION_PLACE, TRANSPORT_IN_STATION_PLACE)  # Waiting in station queue
        self.add_transition(TRANSPORT_IN_STATION_PLACE, TRANSPORT_NEEDS_CHARGING)  # Transition if refused service
        self.add_transition(TRANSPORT_IN_STATION_PLACE, TRANSPORT_IN_WAITING_LIST)  # Moved to waiting list for service

        # Transitions from 'In Waiting List' state
        self.add_transition(TRANSPORT_IN_WAITING_LIST, TRANSPORT_IN_WAITING_LIST)  # Remain in queue
        self.add_transition(TRANSPORT_IN_WAITING_LIST, TRANSPORT_CHARGING)  # Begin charging process

        # Transitions from 'Charging' state
        self.add_transition(TRANSPORT_CHARGING, TRANSPORT_CHARGING)  # Continue charging
        self.add_transition(TRANSPORT_CHARGING, TRANSPORT_WAITING)  # Finish charging and return to waiting

        # Additional transitions for customer movement and destination states
        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_MOVING_TO_CUSTOMER)  # Still en route to customer
        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_WAITING)  # Return to waiting if issue arises
