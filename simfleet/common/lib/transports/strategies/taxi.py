import json
import asyncio

from loguru import logger
from simfleet.utils.abstractstrategies import FSMStrategyBehaviour

from simfleet.common.lib.transports.models.taxi import TaxiStrategyBehaviour
from simfleet.communications.protocol import (
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
from simfleet.utils.utils_old import (
    TRANSPORT_WAITING,
    TRANSPORT_WAITING_FOR_APPROVAL,
    TRANSPORT_MOVING_TO_CUSTOMER,
    TRANSPORT_IN_CUSTOMER_PLACE,
    TRANSPORT_ARRIVED_AT_CUSTOMER,
    CUSTOMER_IN_TRANSPORT,
    TRANSPORT_MOVING_TO_DESTINATION,
    TRANSPORT_ARRIVED_AT_DESTINATION,
    CUSTOMER_IN_DEST
)

################################################################
#                                                              #
#                        Taxi Strategy                         #
#                                                              #
################################################################

class ElectricTaxiWaitingState(TaxiStrategyBehaviour):
    """
        Represents the 'Waiting' state for the electric taxi. The taxi is waiting to receive a transport request.

        Methods:
            on_start(): Sets the initial state to 'TRANSPORT_WAITING' and logs the state.
            run(): Handles incoming messages, processes transport requests, and transitions to the next state.
        """
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

            # New statistics
            # Event 1: Customer Request Reception
            self.agent.events_store.emit(
                event_type="customer_request_reception",
                details={}
            )

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


class TaxiWaitingForApprovalState(TaxiStrategyBehaviour):
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
            # Handle acceptance by the customer or station
            try:
                logger.debug(
                    "Transport {} got accept from {}".format(
                        self.agent.name, content["customer_id"]
                    )
                )

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

                # New statistics - TESTING
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
                    "Transport {} could not get a path to customer {}. Cancelling...".format(
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

class TaxiMovingToCustomerState(TaxiStrategyBehaviour):
    """
        Represents the state where the taxi is moving towards the customer to pick them up.

        Methods:
            on_start(): Logs the transition to 'Moving To Customer'.
            run(): Handles the movement to the customer and manages unexpected issues during the trip.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER
        logger.debug("{} in Transport Moving To Customer State".format(self.agent.jid))

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
                            "Transport {} got refusal from customer/station".format(self.agent.name)
                        )
                        self.agent.status = TRANSPORT_WAITING
                        self.set_next_state(TRANSPORT_WAITING)
                        return

                else:
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


class TaxiArrivedAtCustomerState(TaxiStrategyBehaviour):
    """
        Represents the state where the taxi has arrived at the customer's location.

        Methods:
            on_start(): Logs the transition to 'Arrived At Customer'.
            run(): Handles the pickup of the customer and begins the journey to their destination.
        """

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_ARRIVED_AT_CUSTOMER
        logger.debug("{} in Transport Arrived At Customer State".format(self.agent.jid))

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
                            "Customer {} in transport.".format(self.agent.name)
                        )

                        self.agent.add_customer_in_transport(
                            customer_id=customer_id, dest=dest
                        )
                        await self.agent.remove_assigned_taxicustomer()

                        logger.info(
                            "Transport {} on route to customer destination of {}".format(self.agent.name, customer_id)
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

# MOD-STRATEGY-04 - New status
class TaxiMovingToCustomerDestState(TaxiStrategyBehaviour):
    """
        Represents the state where the taxi is transporting the customer to their destination.

        Methods:
            on_start(): Logs the transition to 'Moving To Destination'.
            run(): Manages the trip to the customer's destination.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_DESTINATION
        logger.debug("{} in Transport Moving To Customer Dest State".format(self.agent.jid))

    async def run(self):

        customers = self.get("current_customer")
        customer_id = next(iter(customers.items()))[0]

        try:

            if not self.agent.is_in_destination():
                await asyncio.sleep(1)
                self.set_next_state(TRANSPORT_MOVING_TO_DESTINATION)
            else:
                logger.info(
                    "Transport {} has arrived to destination. Status: {}".format(
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
                "Transport {} could not get a path to customer {}. Cancelling...".format(
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
                "Unexpected error in transport {}: {}".format(self.agent.name, e)
            )
            await self.cancel_proposal(customer_id)
            self.agent.status = TRANSPORT_WAITING
            self.set_next_state(TRANSPORT_WAITING)
            return

class TaxiArrivedAtCustomerDestState(TaxiStrategyBehaviour):
    """
        Represents the state where the taxi has arrived at the customer's destination.

        Methods:
            on_start(): Logs the transition to 'Arrived At Destination'.
            run(): Handles the process of dropping the customer off and resets the taxi to 'Waiting' state.
        """
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_ARRIVED_AT_DESTINATION
        logger.debug("{} in Transport Arrived at Customer Dest State".format(self.agent.jid))

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
                            "Transport {} has dropped the customer {} in destination.".format(
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


class FSMTaxiStrategyBehaviour(FSMStrategyBehaviour):
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
        self.add_state(TRANSPORT_WAITING_FOR_APPROVAL, TaxiWaitingForApprovalState())
        self.add_state(TRANSPORT_MOVING_TO_CUSTOMER, TaxiMovingToCustomerState())
        self.add_state(TRANSPORT_ARRIVED_AT_CUSTOMER, TaxiArrivedAtCustomerState())
        self.add_state(TRANSPORT_MOVING_TO_DESTINATION, TaxiMovingToCustomerDestState())
        self.add_state(TRANSPORT_ARRIVED_AT_DESTINATION, TaxiArrivedAtCustomerDestState())

        # Define transitions between states

        # Transitions related to the 'Waiting' state
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_WAITING)  # Remains in waiting if no new action
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL)  # When a customer accepts a proposal

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

        # Additional transitions for customer movement and destination states
        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_MOVING_TO_CUSTOMER)  # Still en route to customer
        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_WAITING)  # Return to waiting if issue arises
