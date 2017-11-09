import json

from coordinator import CoordinatorStrategyBehaviour
from passenger import PassengerStrategyBehaviour
from taxi import TaxiStrategyBehaviour
from utils import TAXI_WAITING, REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, coordinator_aid


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
            self.myAgent.send(msg)
            self.logger.debug("Coordinator sent request to taxi {}".format(taxi.getName()))


################################################################
#                                                              #
#                         Taxi Strategy                        #
#                                                              #
################################################################
class AcceptAlwaysStrategyBehaviour(TaxiStrategyBehaviour):
    def _process(self):
        msg = self._receive(block=True)
        content = json.loads(msg.getContent())
        self.logger.debug("Taxi {} received request from passenger {}.".format(self.myAgent.agent_id,
                                                                              content["passenger_id"]))

        if self.myAgent.status == TAXI_WAITING:
            if msg.getPerformative() == REQUEST_PERFORMATIVE:
                self.send_proposal(content["passenger_id"], {})

            elif msg.getPerformative() == ACCEPT_PERFORMATIVE:
                self.pick_up_passenger(content["passenger_id"], content["origin"], content["dest"])


################################################################
#                                                              #
#                       Passenger Strategy                     #
#                                                              #
################################################################
class AcceptFirstRequestTaxiBehaviour(PassengerStrategyBehaviour):
    def _process(self):
        msg = None
        while msg is None and self.myAgent.forceKill() is False:
            self.send_request()
            msg = self.timeout_receive(timeout=5)

        if self.myAgent.forceKill():
            return

        taxi_aid = msg.getSender()
        self.logger.debug("Passenger {} received proposal from {}".format(self.myAgent.agent_id, taxi_aid.getName()))
        self.accept_taxi(taxi_aid)
