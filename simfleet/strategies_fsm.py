import asyncio
import json

from loguru import logger
from spade.behaviour import State, FSMBehaviour

from simfleet.helpers import PathRequestException
from simfleet.protocol import REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE
from simfleet.transport import TransportStrategyBehaviour
from simfleet.utils import TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_MOVING_TO_CUSTOMER


class TransportWaitingState(TransportStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_WAITING

    async def run(self):
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_WAITING)
            return
        logger.info("received: {}".format(msg.body))
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")
        if performative == REQUEST_PERFORMATIVE:
            await self.send_proposal(content["passenger_id"], {})
            self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
            return
        else:
            self.set_next_state(TRANSPORT_WAITING)
            return


class TransportWaitingForApprovalState(TransportStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_WAITING_FOR_APPROVAL

    async def run(self):
        msg = await self.receive(timeout=60)
        if not msg:
            logger.info("No approval msg received. Still waiting.")
            self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
            return
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")
        if performative == ACCEPT_PERFORMATIVE:
            try:
                logger.info("Got accept. Picking up passenger.")
                await self.pick_up_passenger(content["passenger_id"], content["origin"], content["dest"])
                self.set_next_state(TRANSPORT_MOVING_TO_CUSTOMER)
                return
            except PathRequestException:
                await self.cancel_proposal(content["passenger_id"])
                self.set_next_state(TRANSPORT_WAITING)
                return
            except Exception as e:
                await self.cancel_proposal(content["passenger_id"])
                self.set_next_state(TRANSPORT_WAITING)
                return

        elif performative == REFUSE_PERFORMATIVE:
            logger.info("Got refuse :(")
            self.set_next_state(TRANSPORT_WAITING)
            return


passenger_in_transport_event = asyncio.Event()


def passenger_in_transport_callback(old, new):
    if not passenger_in_transport_event.is_set() and new is None:
        passenger_in_transport_event.set()


class TransportMovingState(TransportStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER

    async def run(self):
        passenger_in_transport_event.clear()
        self.agent.watch_value("passenger_in_transport", passenger_in_transport_callback)
        await passenger_in_transport_event.wait()
        logger.info("Transport is free again.")
        return self.set_next_state(TRANSPORT_WAITING)


class FSMTransportStrategyBehaviour(FSMBehaviour):
    def setup(self):
        # Create states
        self.add_state(TRANSPORT_WAITING, TransportWaitingState(), initial=True)
        self.add_state(TRANSPORT_WAITING_FOR_APPROVAL, TransportWaitingForApprovalState())
        self.add_state(TRANSPORT_MOVING_TO_CUSTOMER, TransportMovingState())

        # Create transitions
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_WAITING)
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL)
        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_MOVING_TO_CUSTOMER)
        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_WAITING)
        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_WAITING_FOR_APPROVAL)
        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_WAITING)
