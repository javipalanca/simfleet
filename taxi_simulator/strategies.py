from coordinator import CoordinatorStrategyBehaviour
from passenger import PassengerStrategyBehaviour
from taxi import TaxiStrategyBehaviour
from utils import TAXI_WAITING, TAXI_WAITING_FOR_APPROVAL, PASSENGER_WAITING, TAXI_MOVING_TO_PASSENGER, \
    PASSENGER_ASSIGNED
from protocol import REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, PROPOSE_PERFORMATIVE, \
    CANCEL_PERFORMATIVE
from helpers import coordinator_aid, PathRequestException, content_to_json


################################################################
#                                                              #
#                     Coordinator Strategy                     #
#                                                              #
################################################################
class DelegateRequestTaxiBehaviour(CoordinatorStrategyBehaviour):
    def _process(self):
        msg = self.receive(timeout=60)
        msg.removeReceiver(coordinator_aid)
        for taxi in self.get_taxi_agents():
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
        content = content_to_json(msg)
        performative = msg.getPerformative()

        self.logger.debug("Taxi {} received request protocol from passenger {}.".format(self.myAgent.agent_id,
                                                                                        content["passenger_id"]))
        if performative == REQUEST_PERFORMATIVE:
            if self.myAgent.status == TAXI_WAITING:
                self.send_proposal(content["passenger_id"], {})
                self.myAgent.status = TAXI_WAITING_FOR_APPROVAL

        elif performative == ACCEPT_PERFORMATIVE:
            if self.myAgent.status == TAXI_WAITING_FOR_APPROVAL:
                self.logger.debug("Taxi {} got accept from {}".format(self.myAgent.agent_id,
                                                                      content["passenger_id"]))
                try:
                    self.myAgent.status = TAXI_MOVING_TO_PASSENGER
                    self.pick_up_passenger(content["passenger_id"], content["origin"], content["dest"])
                except PathRequestException:
                    self.logger.error("Taxi {} could not get a path to passenger {}. Cancelling..."
                                      .format(self.myAgent.getName(), content["passenger_id"]))
                    self.myAgent.status = TAXI_WAITING
                    self.cancel_proposal(content["passenger_id"])
                except Exception as e:
                    self.logger.error("Unexpected error in taxi {}: {}".format(self.myAgent.getName(), e))
                    self.cancel_proposal(content["passenger_id"])
                    self.myAgent.status = TAXI_WAITING
            else:
                self.cancel_proposal(content["passenger_id"])

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
            taxi_aid = msg.getSender()
            if performative == PROPOSE_PERFORMATIVE:
                if self.myAgent.status == PASSENGER_WAITING:
                    self.logger.debug("Passenger {} received proposal from taxi {}".format(self.myAgent.agent_id,
                                                                                           taxi_aid.getName()))
                    self.accept_taxi(taxi_aid)
                    self.myAgent.status = PASSENGER_ASSIGNED
                else:
                    self.refuse_taxi(taxi_aid)

            elif performative == CANCEL_PERFORMATIVE:
                if self.myAgent.taxi_assigned == taxi_aid.getName():
                    self.logger.warn("Passenger {} received a CANCEL performative from Taxi {}."
                                     .format(self.myAgent.agent_id, taxi_aid.getName()))
                    self.myAgent.status = PASSENGER_WAITING
