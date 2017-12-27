import json

from coordinator import CoordinatorStrategyBehaviour
from passenger import PassengerStrategyBehaviour
from taxi import TaxiStrategyBehaviour
from utils import TAXI_WAITING, REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, coordinator_aid, \
    TAXI_WAITING_FOR_APPROVAL, REFUSE_PERFORMATIVE, PASSENGER_WAITING, PROPOSE_PERFORMATIVE, CANCEL_PERFORMATIVE, \
    TAXI_MOVING_TO_PASSENGER, PathRequestException


################################################################
#                                                              #
#                     Coordinator Strategy                     #
#                                                              #
################################################################
class DelegateRequestTaxiBehaviour(CoordinatorStrategyBehaviour):
    def _process(self):
        msg = self._receive(block=True)
        msg.removeReceiver(coordinator_aid)
        for taxi in self.myAgent.taxi_agents.values():
            msg.addReceiver(taxi.getAID())
            self.logger.debug("Coordinator sent request to taxi {}".format(taxi.getName()))
        self.myAgent.send(msg)


################################################################
#                                                              #
#                         Taxi Strategy                        #
#                                                              #
################################################################
class AcceptAlwaysStrategyBehaviour(TaxiStrategyBehaviour):
    def _process(self):
        msg = self._receive(block=True)
        content = json.loads(msg.getContent())
        performative = msg.getPerformative()

        self.logger.debug("Taxi {} received request protocol from passenger {}.".format(self.myAgent.agent_id,
                                                                                        content["passenger_id"]))
        if performative == REQUEST_PERFORMATIVE:
            if self.myAgent.status == TAXI_WAITING:
                self.send_proposal(content["passenger_id"], {})
                self.myAgent.status = TAXI_WAITING_FOR_APPROVAL

                self.logger.debug("Taxi {} sent proposal to passenger {}.".format(self.myAgent.agent_id,
                                                                                  content["passenger_id"]))

        elif performative == ACCEPT_PERFORMATIVE:
            if self.myAgent.status == TAXI_WAITING_FOR_APPROVAL:
                self.logger.debug("Taxi {} got accept from {}".format(self.myAgent.agent_id,
                                                                      content["passenger_id"]))
                try:
                    self.pick_up_passenger(content["passenger_id"], content["origin"], content["dest"])
                    self.myAgent.status = TAXI_MOVING_TO_PASSENGER
                except PathRequestException:
                    self.cancel_proposal(content["passenger_id"], {})
                    self.myAgent.status = TAXI_WAITING
            else:
                self.cancel_proposal(content["passenger_id"], {})

        elif performative == REFUSE_PERFORMATIVE:
            self.logger.debug("Taxi {} got refusal from {}".format(self.myAgent.agent_id,
                                                                   content["passenger_id"]))
            self.myAgent.status = TAXI_WAITING


################################################################
#                                                              #
#                       Passenger Strategy                     #
#                                                              #
################################################################
class AcceptFirstRequestTaxiBehaviour(PassengerStrategyBehaviour):
    def _process(self):
        if self.myAgent.status == PASSENGER_WAITING:
            self.send_request(content={})

        msg = self.timeout_receive(timeout=5)

        if msg:
            performative = msg.getPerformative()
            if performative == PROPOSE_PERFORMATIVE:
                taxi_aid = msg.getSender()
                if self.myAgent.status == PASSENGER_WAITING:
                    self.logger.debug("Passenger {} received proposal from {}".format(self.myAgent.agent_id,
                                                                                      taxi_aid.getName()))
                    self.accept_taxi(taxi_aid)
                else:
                    self.refuse_taxi(taxi_aid)

            elif performative == CANCEL_PERFORMATIVE:
                self.myAgent.status = PASSENGER_WAITING
