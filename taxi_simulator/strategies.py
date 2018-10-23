import json

from .coordinator import CoordinatorStrategyBehaviour
from .passenger import PassengerStrategyBehaviour
from .taxi import TaxiStrategyBehaviour
from .utils import TAXI_WAITING, TAXI_WAITING_FOR_APPROVAL, PASSENGER_WAITING, TAXI_MOVING_TO_PASSENGER, \
    PASSENGER_ASSIGNED
from .protocol import REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, PROPOSE_PERFORMATIVE, \
    CANCEL_PERFORMATIVE
from .helpers import PathRequestException


################################################################
#                                                              #
#                     Coordinator Strategy                     #
#                                                              #
################################################################
class DelegateRequestTaxiBehaviour(CoordinatorStrategyBehaviour):
    """
    The default strategy for the Coordinator agent. By default it delegates all requests to all taxis.
    """

    async def run(self):
        msg = await self.receive(timeout=5)
        if msg:
            for taxi in self.get_taxi_agents():
                msg.to = str(taxi.jid)
                self.logger.debug("Coordinator sent request to taxi {}".format(taxi.name))
                await self.send(msg)


################################################################
#                                                              #
#                         Taxi Strategy                        #
#                                                              #
################################################################
class AcceptAlwaysStrategyBehaviour(TaxiStrategyBehaviour):
    """
    The default strategy for the Taxi agent. By default it accepts every request it receives if available.
    """

    async def run(self):
        msg = await self.receive(timeout=5)
        if not msg:
            return
        self.logger.debug("Taxi received message: {}".format(msg))
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")

        self.logger.debug("Taxi {} received request protocol from passenger {}.".format(self.agent.name,
                                                                                        content["passenger_id"]))
        if performative == REQUEST_PERFORMATIVE:
            if self.agent.status == TAXI_WAITING:
                await self.send_proposal(content["passenger_id"], {})
                self.agent.status = TAXI_WAITING_FOR_APPROVAL

        elif performative == ACCEPT_PERFORMATIVE:
            if self.agent.status == TAXI_WAITING_FOR_APPROVAL:
                self.logger.debug("Taxi {} got accept from {}".format(self.agent.name,
                                                                      content["passenger_id"]))
                try:
                    self.agent.status = TAXI_MOVING_TO_PASSENGER
                    await self.pick_up_passenger(content["passenger_id"], content["origin"], content["dest"])
                except PathRequestException:
                    self.logger.error("Taxi {} could not get a path to passenger {}. Cancelling..."
                                      .format(self.agent.name, content["passenger_id"]))
                    self.agent.status = TAXI_WAITING
                    await self.cancel_proposal(content["passenger_id"])
                except Exception as e:
                    self.logger.error("Unexpected error in taxi {}: {}".format(self.agent.name, e))
                    await self.cancel_proposal(content["passenger_id"])
                    self.agent.status = TAXI_WAITING
            else:
                await self.cancel_proposal(content["passenger_id"])

        elif performative == REFUSE_PERFORMATIVE:
            self.logger.debug("Taxi {} got refusal from {}".format(self.agent.name,
                                                                   content["passenger_id"]))
            if self.agent.status == TAXI_WAITING_FOR_APPROVAL:
                self.agent.status = TAXI_WAITING


################################################################
#                                                              #
#                       Passenger Strategy                     #
#                                                              #
################################################################
class AcceptFirstRequestTaxiBehaviour(PassengerStrategyBehaviour):
    """
    The default strategy for the Passenger agent. By default it accepts the first proposal it receives.
    """

    async def run(self):
        if self.agent.status == PASSENGER_WAITING:
            await self.send_request(content={})

        msg = await self.receive(timeout=5)

        if msg:
            performative = msg.get_metadata("performative")
            taxi_id = msg.sender
            if performative == PROPOSE_PERFORMATIVE:
                if self.agent.status == PASSENGER_WAITING:
                    self.logger.debug("Passenger {} received proposal from taxi {}".format(self.agent.name,
                                                                                           taxi_id))
                    await self.accept_taxi(taxi_id)
                    self.agent.status = PASSENGER_ASSIGNED
                else:
                    await self.refuse_taxi(taxi_id)

            elif performative == CANCEL_PERFORMATIVE:
                if self.agent.taxi_assigned == str(taxi_id):
                    self.logger.warning("Passenger {} received a CANCEL from Taxi {}.".format(self.agent.name, taxi_id))
                    self.agent.status = PASSENGER_WAITING
