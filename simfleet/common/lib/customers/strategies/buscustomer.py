import asyncio
import json
import time

from loguru import logger

from simfleet.utils.abstractstrategies import FSMSimfleetBehaviour

from simfleet.common.lib.customers.models.buscustomer import BusCustomerStrategyBehaviour

from simfleet.utils.status import CUSTOMER_WAITING, CUSTOMER_WAITING_TO_MOVE, CUSTOMER_IN_TRANSPORT, CUSTOMER_MOVING_TO_DEST, \
    CUSTOMER_IN_DEST, CUSTOMER_IN_STOP, CUSTOMER_WAITING_FOR_APPROVAL

from simfleet.communications.protocol import (
    INFORM_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
)

from simfleet.utils.helpers import (
    PathRequestException,
    AlreadyInDestination
)

################################################################
#                                                              #
#                   BusCustomer Strategy                       #
#                                                              #
################################################################

class BusCustomerWaitingToMoveState(BusCustomerStrategyBehaviour):
    """
        Represents the state where the customer is waiting to move to the bus stop.
    """

    async def on_start(self):
        await super().on_start()
        self.agent.status = CUSTOMER_WAITING_TO_MOVE
        logger.debug("Customer {} in BusCustomerWaitingToMoveState".format(self.agent.name))

    async def run(self):
        """
            Manages the movement of the customer to the bus stop.
        """

        if self.agent.stop_dic is None:
            # Obtain the list of bus stops if not available
            self.agent.stop_dic = await self.agent.get_list_agent_position(self.agent.type_service, self.agent.stop_dic)

            self.set_next_state(CUSTOMER_WAITING_TO_MOVE)
            return
        else:

            self.setup_stops()

            if self.agent.current_stop[1] != self.agent.get("current_pos"):
                self.agent.pedestrian_dest = self.agent.current_stop[1]

                logger.info(
                    "Agent {} on route to destination {}".format(self.agent.name, self.agent.current_stop[1])
                )

                try:
                    logger.debug("{} move_to destination {}".format(self.agent.name, self.agent.current_stop[1]))

                    await self.agent.move_to(self.agent.current_stop[1])
                    self.set_next_state(CUSTOMER_MOVING_TO_DEST)
                except AlreadyInDestination:
                    logger.debug(
                        "{} is already in the destination' {} position. . .".format(
                            self.agent.name, self.agent.current_stop[1]
                        )
                    )
                    self.set_next_state(CUSTOMER_WAITING_TO_MOVE)

            else:
                self.set_next_state(CUSTOMER_IN_STOP)



class BusCustomerRegisterToStopState(BusCustomerStrategyBehaviour):
    """
        Represents the state where the customer registers at the bus stop.
    """

    async def on_start(self):
        await super().on_start()
        self.agent.status = CUSTOMER_IN_STOP
        logger.debug("Customer {} in CustomerRegisterToStopState".format(self.agent.name))

    async def run(self):

        # Send registration petition to the bus stop
        self.agent.arguments["jid"] = str(self.agent.jid)
        self.agent.arguments["destination_stop"] = self.agent.destination_stop[1]

        content = {"line": self.agent.line, "object_type": "customer", "args": self.agent.arguments}
        await self.register_to_stop(content)
        # Wait for registration acceptance
        msg = await self.receive(timeout=30)

        if msg:
            sender = str(msg.sender)
            performative = msg.get_metadata("performative")
            if performative == ACCEPT_PERFORMATIVE:
                self.agent.registered_in = sender
                logger.info("Customer {} registered in bus stop {}".format(self.agent.name, sender))
                self.set_next_state(CUSTOMER_WAITING)
                return
        else:
            self.set_next_state(CUSTOMER_IN_STOP)
            return

class BusCustomerMovingToDestState(BusCustomerStrategyBehaviour):
    """
        Represents the state where the customer moves towards the destination.
    """
    async def on_start(self):
        await super().on_start()
        self.agent.status = CUSTOMER_MOVING_TO_DEST
        logger.debug("Customer {} in BusCustomerMovingToDestState".format(self.agent.name))

    async def run(self):
        """
            Handles the movement to the destination and transitions to the next state up on arrival.
        """
        try:
            if not self.agent.get_position() == self.agent.pedestrian_dest:
                await asyncio.sleep(1)
                self.set_next_state(CUSTOMER_MOVING_TO_DEST)
            else:

                if not self.agent.get_position() == self.agent.customer_dest:
                    self.set_next_state(CUSTOMER_IN_STOP)
                else:
                    self.set_next_state(CUSTOMER_IN_DEST)

        except AlreadyInDestination:
            logger.warning(
                "Customer {} has arrived to destination: {}.".format(
                    self.agent.agent_id, self.agent.is_in_destination()
                )
            )
            if not self.agent.get_position() == self.agent.customer_dest:
                self.set_next_state(CUSTOMER_IN_STOP)
            else:
                self.set_next_state(CUSTOMER_IN_DEST)
            return
        except PathRequestException:
            logger.error(
                "Transport {} could not get a path to customer. Cancelling...".format(
                    self.agent.name
                )
            )
            self.set_next_state(CUSTOMER_WAITING_TO_MOVE)
            return

class BusCustomerWaitingState(BusCustomerStrategyBehaviour):
    """
        Represents the state where the customer is waiting for a transport after registering at the stop.
    """
    async def on_start(self):
        await super().on_start()
        self.agent.status = CUSTOMER_WAITING
        logger.debug("Customer {} in CustomerWaitingState".format(self.agent.name))

    async def run(self):
        try:
            logger.info("Customer {} waiting for a transport to {}".format(self.agent.name, self.agent.destination_stop[1]))
            self.agent.alternative_transports = []
            msg = await self.receive(timeout=60)
            if msg:
                sender = msg.sender
                performative = msg.get_metadata("performative")
                logger.debug(
                    "Customer {} received message {} from bus stop {}".format(self.agent.name, msg.body, sender))
                contents = json.loads(msg.body)
                if performative == INFORM_PERFORMATIVE:
                    # send message to board the transport
                    logger.info("Customer {} sending message to board transport {}".format(self.agent.name,
                                                                                            contents.get("transport")))
                    await self.board_transport(contents["transport"])
                    self.set_next_state(CUSTOMER_WAITING_FOR_APPROVAL)
                    return
            else:
                self.set_next_state(CUSTOMER_WAITING)
                return
        except Exception as e:
            logger.critical("Agent {}, Exception {} in CustomerWaitingState".format(self.agent.name, e))


class BusCustomerWaitingForApprovalState(BusCustomerStrategyBehaviour):
    """
        Represents the state where the customer is waiting for approval to board the transport.

    """

    async def on_start(self):
        await super().on_start()
        self.agent.status = CUSTOMER_WAITING_FOR_APPROVAL
        logger.debug("Customer {} in CustomerWaitingForApprovalState".format(self.agent.name))

    async def run(self):
        try:
            msg = await self.receive(timeout=10)
            if msg:
                sender = msg.sender
                sender = str(sender)
                performative = msg.get_metadata("performative")
                contents = json.loads(msg.body)
                logger.debug(
                    "Customer {} received message {} from transport {}".format(self.agent.name, contents, sender))
                if performative == ACCEPT_PERFORMATIVE:  # transport has enough capacity, board the transport
                    logger.info("Customer {} boarding transport {}".format(self.agent.name, sender))
                    content = {"line": self.agent.line}
                    await self.inform_stop(content)
                    self.agent.set("current_transport", sender)
                    self.set_next_state(CUSTOMER_IN_TRANSPORT)
                    return
                elif performative == REFUSE_PERFORMATIVE:  # transport is full, rejects customer boarding
                    logger.info("Customer {} rejected by transport {}".format(self.agent.name, sender))
                    # look for an alternative transport
                    if len(self.agent.alternative_transports) > 0:
                        board_to = self.agent.alternative_transports[0]
                        self.agent.alternative_transports = self.agent.alternative_transports[1:]
                        logger.info("Customer {} sending message to board alternative transport {}".format(
                            self.agent.name, board_to))
                        await self.board_transport(board_to)
                        self.set_next_state(CUSTOMER_WAITING_FOR_APPROVAL)
                    else:
                        self.set_next_state(CUSTOMER_WAITING)
                    return
                elif performative == INFORM_PERFORMATIVE:  # the stop is telling me there is another bus
                    logger.info("Customer {} informed of alternative transport {} by stop {}".format(self.agent.name,
                                                                                                     contents["transport"],
                                                                                                     sender))
                    self.agent.alternative_transports.append(contents["transport"])
                    logger.debug("Customer's {} alternative transports: {}".format(
                        self.agent.name, self.agent.alternative_transports))
                    self.set_next_state(CUSTOMER_WAITING_FOR_APPROVAL)
                else:
                    logger.warning("Customer {} received unexpected message {}".format(self.agent.name, msg))
                    self.set_next_state(CUSTOMER_WAITING)
                    logger.error("Customer {} going back to CUSTOMER_WAITING state".format(self.agent.name))
                    return
            else:
                self.set_next_state(CUSTOMER_WAITING)
                return
        except Exception as e:
            logger.critical("Agent {}, Exception {} in CustomerWaitingForApprovalState".format(self.agent.name, e))


class BusCustomerInTransportState(BusCustomerStrategyBehaviour):
    """
        Represents the state where the customer is in the transport.

    """

    async def on_start(self):
        await super().on_start()
        self.agent.status = CUSTOMER_IN_TRANSPORT
        logger.debug("Customer {} in CustomerInTransportState".format(self.agent.name))
        # Compute time waiting to board a transport

    async def run(self):
        try:
            # TODO (future) awake the customer each time the bus gets to a stop and let customer decide what to do
            self.agent.customer_arrived_to_destination_event.clear()
            self.agent.watch_value("arrived_to_destination", self.agent.customer_arrived_to_destination_callback)
            await self.agent.customer_arrived_to_destination_event.wait()
            return self.set_next_state(CUSTOMER_IN_DEST)
        except Exception as e:
            logger.critical("Agent {}, Exception {} in CustomerInTransportState".format(self.agent.name, e))


class BusCustomerInDestState(BusCustomerStrategyBehaviour):
    """
        Represents the state where the customer has arrived at the destination.

    """
    async def on_start(self):
        await super().on_start()
        self.agent.status = CUSTOMER_IN_DEST
        logger.debug("Customer {} in CustomerInDestState".format(self.agent.name))

    async def run(self):
        try:
            # wait for the transport to inform the customer that the destination stop has been reached
            msg = await self.receive(timeout=10)
            if msg:

                performative = msg.get_metadata("performative")
                if performative == INFORM_PERFORMATIVE:
                    logger.info("Customer {} has reached their destination".format(self.agent.name))

                    if self.agent.destination_stop[1] != self.agent.customer_dest:

                        self.agent.pedestrian_dest = self.agent.customer_dest

                        logger.info(
                            "Agent {} on route to destination {}".format(self.agent.name, self.agent.customer_dest)
                        )

                        try:
                            logger.debug("{} move_to destination {}".format(self.agent.name, self.agent.customer_dest))

                            await self.agent.move_to(self.agent.customer_dest)
                            self.set_next_state(CUSTOMER_MOVING_TO_DEST)
                            return
                        except AlreadyInDestination:
                            logger.debug(
                                "{} is already in the destination' {} position. . .".format(
                                    self.agent.name, self.agent.customer_dest
                                )
                            )
                            self.set_next_state(CUSTOMER_IN_DEST)
                            return
            self.set_next_state(CUSTOMER_IN_DEST)
            return
        except Exception as e:
            logger.critical("Agent {}, Exception {} in CustomerInDestState".format(self.agent.name, e))


class FSMBusCustomerBehaviour(FSMSimfleetBehaviour):
    """
        The finite state machine that orchestrates the different states for the bus customer strategy.
    """
    def setup(self):
        # Create states
        self.add_state(CUSTOMER_WAITING_TO_MOVE, BusCustomerWaitingToMoveState(), initial=True)
        self.add_state(CUSTOMER_MOVING_TO_DEST, BusCustomerMovingToDestState())
        self.add_state(CUSTOMER_IN_STOP, BusCustomerRegisterToStopState())
        self.add_state(CUSTOMER_WAITING, BusCustomerWaitingState())
        self.add_state(CUSTOMER_WAITING_FOR_APPROVAL, BusCustomerWaitingForApprovalState())
        self.add_state(CUSTOMER_IN_TRANSPORT, BusCustomerInTransportState())
        self.add_state(CUSTOMER_IN_DEST, BusCustomerInDestState())

        # Create transitions
        self.add_transition(CUSTOMER_WAITING_TO_MOVE, CUSTOMER_WAITING_TO_MOVE)
        self.add_transition(CUSTOMER_WAITING_TO_MOVE, CUSTOMER_IN_STOP)
        self.add_transition(CUSTOMER_WAITING_TO_MOVE, CUSTOMER_MOVING_TO_DEST)
        self.add_transition(CUSTOMER_MOVING_TO_DEST, CUSTOMER_MOVING_TO_DEST)
        self.add_transition(CUSTOMER_MOVING_TO_DEST, CUSTOMER_WAITING_TO_MOVE)
        self.add_transition(CUSTOMER_MOVING_TO_DEST, CUSTOMER_IN_DEST)
        self.add_transition(CUSTOMER_MOVING_TO_DEST, CUSTOMER_IN_STOP)
        self.add_transition(CUSTOMER_IN_STOP, CUSTOMER_IN_STOP)
        self.add_transition(CUSTOMER_IN_STOP, CUSTOMER_WAITING)
        self.add_transition(CUSTOMER_WAITING, CUSTOMER_WAITING)
        self.add_transition(CUSTOMER_WAITING, CUSTOMER_WAITING_FOR_APPROVAL)
        self.add_transition(CUSTOMER_WAITING_FOR_APPROVAL, CUSTOMER_WAITING)
        self.add_transition(CUSTOMER_WAITING_FOR_APPROVAL, CUSTOMER_WAITING_FOR_APPROVAL)
        self.add_transition(CUSTOMER_WAITING_FOR_APPROVAL, CUSTOMER_IN_TRANSPORT)
        self.add_transition(CUSTOMER_IN_TRANSPORT, CUSTOMER_IN_DEST)
        self.add_transition(CUSTOMER_IN_DEST, CUSTOMER_IN_DEST)
        self.add_transition(CUSTOMER_IN_DEST, CUSTOMER_MOVING_TO_DEST)
