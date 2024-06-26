import json
import time

from loguru import logger
from spade.behaviour import State, FSMBehaviour

from simfleet.common.extensions.transports.models.bus import BusStrategyBehaviour

from simfleet.utils.utils_old import (
    TRANSPORT_WAITING,
    TRANSPORT_NEEDS_CHARGING,
    TRANSPORT_WAITING_FOR_APPROVAL,
    TRANSPORT_MOVING_TO_STATION,
    TRANSPORT_IN_STATION_PLACE,
    TRANSPORT_IN_WAITING_LIST,
    TRANSPORT_CHARGING,
    TRANSPORT_CHARGED,
    TRANSPORT_MOVING_TO_CUSTOMER,
    TRANSPORT_IN_CUSTOMER_PLACE,
    TRANSPORT_ARRIVED_AT_CUSTOMER,
    TRANSPORT_MOVING_TO_DESTINATION,
    TRANSPORT_ARRIVED_AT_DESTINATION,
    TRANSPORT_IN_DEST,
    TRANSPORT_BOARDING,
)

from simfleet.communications.protocol import (
    INFORM_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    REQUEST_PERFORMATIVE,
    QUERY_PROTOCOL
)



################################################################
#                                                              #
#                            Bus Strategy                      #
#                                                              #
################################################################

class BusSelectDestState(BusStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_WAITING
        logger.debug("Transport {} in TransportSelectDestState".format(self.agent.name))

    async def run(self):
        if self.agent.stop_dic is None:
            await self.send_get_stops()

            msg = await self.receive(timeout=300)       #Director envia informacion de las paradas
            if msg:
                protocol = msg.get_metadata("protocol")
                if protocol == QUERY_PROTOCOL:
                    performative = msg.get_metadata("performative")
                    if performative == INFORM_PERFORMATIVE:
                        self.agent.stop_dic = json.loads(msg.body)
                        logger.debug(
                            "{} got stops {}".format(
                                self.agent.name, self.agent.stop_dic
                            )
                        )
                        self.agent.setup_current_stop()
                    elif performative == CANCEL_PERFORMATIVE:
                        logger.warning(
                            "{} got cancellation of request for {} information".format(
                                self.agent.name, self.agent.type_service
                            )
                        )
            self.set_next_state(TRANSPORT_WAITING)
            return

        logger.debug("Transport {} in position {} within its stop_list ({})".format(self.agent.jid,
                                                                                    self.agent.get("current_pos"),
                                                                                    self.agent.stop_list))
        # get next destination (coords) in the list of destinations
        next_destination = self.get_subsequent_stop()
        # if current destination is the end of a route
        if next_destination is None:
            logger.warning(
                "Transport {} has reached the last stop in its line {}".format(self.agent.jid, self.agent.line))
            # Increase number of rounds (complete traversal of the transport's stops)
            self.agent.rounds += 1
            # choose first stop of the route as next destination (circular routes)
            if self.agent.line_type == "circular":
                logger.warning("Transport {} repeating its circular line".format(self.agent.jid))
                next_destination = self.agent.stop_list[0]
            # inverse stop list and choose previous destination as next destination (end-to-end lines)
            if self.agent.line_type == "end-to-end":
                logger.warning("Transport {} reversing its end-to-end line".format(self.agent.jid))
                self.agent.stop_list.reverse()
                next_destination = self.get_subsequent_stop()
            # "teleport" bus to first stop and choose next destination
            if self.agent.line_type == "teleport":
                logger.warning("Transport {} teleporting to its first stop".format(self.agent.jid))
                first_stop_coords = self.agent.stop_list[0]
                self.agent.set("current_pos", first_stop_coords)
                next_destination = self.agent.get("current_pos")
        # move to next destination
        if next_destination is None:
            logger.critical("Transport {} with line {} and line_type {} could not get a next destination".format(
                self.agent.name, self.agent.line, self.agent.line_type
            ))
            exit()
        await self.move_to_next_stop(next_destination)
        self.set_next_state(TRANSPORT_MOVING_TO_DESTINATION)
        return


class BusMovingToDestState(BusStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_DESTINATION
        logger.debug("Transport {} in TransportMovingToDestState".format(self.agent.name))

    async def run(self):
        if self.agent.is_in_destination():
            return self.set_next_state(TRANSPORT_IN_DEST)
        # Reset internal flag to False. Coroutines calling wait() will block until set() is called
        self.agent.transport_arrived_to_stop_event.clear()
        # Register an observer callback to be run when the "arrived_to_stop" event is changed
        self.agent.watch_value("arrived_to_stop", self.agent.transport_arrived_to_stop_callback)
        # block behaviour until another coroutine calls set()
        await self.agent.transport_arrived_to_stop_event.wait()
        return self.set_next_state(TRANSPORT_IN_DEST)


class BusInDestState(BusStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_IN_DEST
        logger.debug("Transport {} in TransportInDestState".format(self.agent.name))

    async def run(self):
        # Write occupation statistics
        #self.agent.occupations.append(len(self.agent.current_customers))
        self.agent.occupations.append(len(self.agent.get("current_customer")))
        # Drop off customers who are at their destination
        await self.drop_customers()
        # Inform the stop the boarding may begin
        content = {"line": self.agent.line, "list_of_stops": self.agent.stop_list}
        await self.begin_boarding(content)
        return self.set_next_state(TRANSPORT_BOARDING)


class BusBoardingCustomersState(BusStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_BOARDING
        logger.debug("Transport {} in TransportBoardingCustomersState".format(self.agent.name))

    async def run(self):
        # Accept new passengers one by one, updating capacity
        msg = await self.receive(timeout=5)
        if msg:
            sender = msg.sender
            content = json.loads(msg.body)
            performative = msg.get_metadata("performative")
            if performative == REQUEST_PERFORMATIVE:
                if self.agent.current_capacity > 0:
                    await self.accept_customer(sender, content)
                    self.agent.current_capacity -= 1
                    logger.info("Transport {} current capacity is {}".format(self.agent.name,
                                                                             self.agent.current_capacity))
                else:  # transport is full, can not board more passengers
                    await self.reject_customer(sender, content)
            # unexpected message received, loop
            return self.set_next_state(TRANSPORT_BOARDING)
        # no message received, go to select next destination
        return self.set_next_state(TRANSPORT_WAITING)


class FSMBusStrategyBehaviour(FSMBehaviour):
    def setup(self):
        # Create states
        self.add_state(TRANSPORT_WAITING, BusSelectDestState(), initial=True)
        self.add_state(TRANSPORT_MOVING_TO_DESTINATION, BusMovingToDestState())
        self.add_state(TRANSPORT_IN_DEST, BusInDestState())
        self.add_state(TRANSPORT_BOARDING, BusBoardingCustomersState())
        # Create transitions
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_WAITING)
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_MOVING_TO_DESTINATION)
        self.add_transition(TRANSPORT_MOVING_TO_DESTINATION, TRANSPORT_IN_DEST)
        self.add_transition(TRANSPORT_IN_DEST, TRANSPORT_BOARDING)
        self.add_transition(TRANSPORT_BOARDING, TRANSPORT_BOARDING)
        self.add_transition(TRANSPORT_BOARDING, TRANSPORT_WAITING)
