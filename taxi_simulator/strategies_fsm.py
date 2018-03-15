import threading
import time

from taxi_simulator.fsm import State, StateMachine
from taxi_simulator.helpers import content_to_json, PathRequestException
from taxi_simulator.protocol import REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE
from taxi_simulator.taxi import TaxiStrategyBehaviour
from taxi_simulator.utils import TAXI_WAITING, TAXI_WAITING_FOR_APPROVAL, TAXI_MOVING_TO_PASSENGER


class TaxiWaitingState(State):

    def run(self):
        msg = self.receive(timeout=60)
        if not msg:
            return
        self.logger.info("received: {}".format(msg.getContent()))
        content = content_to_json(msg)
        performative = msg.getPerformative()
        if performative == REQUEST_PERFORMATIVE:
            self.helpers.send_proposal(content["passenger_id"], {})
            return self.transition_to(TAXI_WAITING_FOR_APPROVAL)


class TaxiWaitingForApprovalState(State):

    def run(self):
        msg = self.receive(timeout=60)
        if not msg:
            self.logger.info("No approval msg received. Still waiting.")
            return
        content = content_to_json(msg)
        performative = msg.getPerformative()
        if performative == ACCEPT_PERFORMATIVE:
            try:
                self.logger.info("Got accept. Picking up passenger.")
                self.helpers.pick_up_passenger(content["passenger_id"], content["origin"], content["dest"])
                return self.transition_to(TAXI_MOVING_TO_PASSENGER)
            except PathRequestException:
                self.helpers.cancel_proposal(content["passenger_id"])
                return self.transition_to(TAXI_WAITING)
            except Exception as e:
                self.helpers.cancel_proposal(content["passenger_id"])
                return self.transition_to(TAXI_WAITING)

        elif performative == REFUSE_PERFORMATIVE:
            self.logger.info("Got refuse :(")
            return self.transition_to(TAXI_WAITING)


passenger_in_taxi_event = threading.Event()


def passenger_in_taxi_callback(old, new):
    if not passenger_in_taxi_event.is_set():
        passenger_in_taxi_event.set()


class TaxiMovingState(State):
    def run(self):
        passenger_in_taxi_event.clear()
        self.behav.myAgent.watch_value("passenger_in_taxi", passenger_in_taxi_callback)
        passenger_in_taxi_event.wait()
        self.logger.info("Taxi is free again.")
        return self.transition_to(TAXI_WAITING)


class TaxiStrategy(StateMachine):
    def setup(self):
        # Create states
        self.register_state(TaxiWaitingState(TAXI_WAITING))
        self.register_state(TaxiWaitingForApprovalState(TAXI_WAITING_FOR_APPROVAL))
        self.register_state(TaxiMovingState(TAXI_MOVING_TO_PASSENGER))

        # Initial state
        self.set_initial_state(initial_state_name=TAXI_WAITING)


class FSMTaxiStrategyBehaviour(TaxiStrategyBehaviour):

    def onStart(self):
        self.myAgent.fsm = TaxiStrategy(self)
        TaxiStrategyBehaviour.onStart(self)

    def _process(self):
        while not self.myAgent.fsm.is_finished():
            self.myAgent.fsm.step()
        self.myAgent.fsm.current_state.run()
        self.kill()
