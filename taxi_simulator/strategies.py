import json

from .fleetmanager import CoordinatorStrategyBehaviour
from .customer import CustomerStrategyBehaviour
from .transport import TransportStrategyBehaviour
from .secretary import SecretaryStrategyBehaviour
from .station import StationStrategyBehaviour
from .utils import TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL, CUSTOMER_WAITING, TRANSPORT_MOVING_TO_CUSTOMER, \
    CUSTOMER_ASSIGNED, TRANSPORT_WAITING_FOR_STATION_APPROVAL, FREE_STATION, TRANSPORT_MOVING_TO_STATION, TRANSPORT_LOADING, TRANSPORT_LOADED
from .protocol import REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, PROPOSE_PERFORMATIVE, \
    CANCEL_PERFORMATIVE, INFORM_PERFORMATIVE, CONFIRM_PERFORMATIVE
from .helpers import PathRequestException


################################################################
#                                                              #
#                     FleetManager Strategy                    #
#                                                              #
################################################################
class DelegateRequestTaxiBehaviour(CoordinatorStrategyBehaviour):
    """
    The default strategy for the FleetManager agent. By default it delegates all requests to all transports.
    """

    async def run(self):
        if not self.agent.registration:
            await self.send_registration()

        msg = await self.receive(timeout=5)
        self.logger.debug("Manager received message: {}".format(msg))
        if msg:
            for transport in self.get_transport_agents().values():
                msg.to = str(transport["jid"])
                self.logger.debug("Manager sent request to transport {}".format(transport["name"]))
                await self.send(msg)


################################################################
#                                                              #
#                     Transport Strategy                       #
#                                                              #
################################################################
class AcceptAlwaysStrategyBehaviour(TransportStrategyBehaviour):
    """
    The default strategy for the Taxi agent. By default it accepts every request it receives if available.
    """

    async def run(self):
        if not self.agent.registration:
            await self.send_registration()

        if self.agent.get_fuel() < 40 and not self.agent.flag_stations:
            await self.send_get_stations()

        msg = await self.receive(timeout=5)
        if not msg:
            return
        self.logger.debug("Transport received message: {}".format(msg))
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")

        self.logger.debug("Transport {} received request protocol from customer/station.".format(self.agent.name))

        if performative == REQUEST_PERFORMATIVE:
            if self.agent.status == TRANSPORT_WAITING:
                if not self.do_travel(content["origin"], content["dest"]):
                    await self.cancel_proposal(content["customer_id"])
                    self.agent.status = TRANSPORT_WAITING_FOR_STATION_APPROVAL
                    for station in self.agent.stations:
                        await self.send_proposal(station)
                else:
                    await self.send_proposal(content["customer_id"], {})
                    self.agent.status = TRANSPORT_WAITING_FOR_APPROVAL

        elif performative == ACCEPT_PERFORMATIVE:
            if self.agent.status == TRANSPORT_WAITING_FOR_APPROVAL:
                self.logger.debug("Transport {} got accept from {}".format(self.agent.name,
                                                                      content["customer_id"]))
                try:
                    self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER
                    await self.pick_up_customer(content["customer_id"], content["origin"], content["dest"])
                except PathRequestException:
                    self.logger.error("Transport {} could not get a path to customer {}. Cancelling..."
                                      .format(self.agent.name, content["customer_id"]))
                    self.agent.status = TRANSPORT_WAITING
                    await self.cancel_proposal(content["customer_id"])
                except Exception as e:
                    self.logger.error("Unexpected error in transport {}: {}".format(self.agent.name, e))
                    await self.cancel_proposal(content["customer_id"])
                    self.agent.status = TRANSPORT_WAITING
            else:
                await self.cancel_proposal(content["customer_id"])

        elif performative == CONFIRM_PERFORMATIVE:
            if self.agent.status == TRANSPORT_WAITING_FOR_STATION_APPROVAL:
                self.logger.info("Transport {} got accept from station {}".format(self.agent.name,
                                                                                  content["station_id"]))
                try:
                    self.agent.status = TRANSPORT_MOVING_TO_STATION
                    await self.go_to_the_station(content["station_id"], content["dest"])
                except PathRequestException:
                    self.logger.error("Transport {} could not get a path to station {}. Cancelling..."
                                      .format(self.agent.name, content["station_id"]))
                    self.agent.status = TRANSPORT_WAITING
                    await self.cancel_proposal(content["station_id"])
                except Exception as e:
                    self.logger.error("Unexpected error in transport {}: {}".format(self.agent.name, e))
                    await self.cancel_proposal(content["station_id"])
                    self.agent.status = TRANSPORT_WAITING
            elif self.agent.status == TRANSPORT_LOADING:
                if content["status"] == TRANSPORT_LOADED:
                    self.agent.transport_loaded()
                    await self.agent.drop_station()

        elif performative == REFUSE_PERFORMATIVE:
            self.logger.debug("Transport {} got refusal from customer/station".format(self.agent.name))
            if self.agent.status == TRANSPORT_WAITING_FOR_APPROVAL or self.agent.status == TRANSPORT_WAITING_FOR_STATION_APPROVAL:
                self.agent.status = TRANSPORT_WAITING

        elif performative == INFORM_PERFORMATIVE:
            self.agent.stations = json.loads(msg.body)
            self.logger.debug("Registration of current stations {}".format(self.agent.stations))

        elif performative == CANCEL_PERFORMATIVE:
            self.logger.info(
                "Cancellation of request for {} information".format(self.agent.type_service))


################################################################
#                                                              #
#                       Customer Strategy                      #
#                                                              #
################################################################
class AcceptFirstRequestTaxiBehaviour(CustomerStrategyBehaviour):
    """
    The default strategy for the Customer agent. By default it accepts the first proposal it receives.
    """

    async def run(self):
        if self.agent.fleetmanagers is None:
            await self.send_get_managers(content="")

            msg = await self.receive(timeout=5)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == INFORM_PERFORMATIVE:
                    self.agent.fleetmanagers = json.loads(msg.body)
                    return
                elif performative == CANCEL_PERFORMATIVE:
                    self.logger.info("Cancellation of request for {} information".format(self.agent.type_service))
                    return

        if self.agent.status == CUSTOMER_WAITING:
            await self.send_request(content={})

        msg = await self.receive(timeout=5)

        if msg:
            performative = msg.get_metadata("performative")
            transport_id = msg.sender
            if performative == PROPOSE_PERFORMATIVE:
                if self.agent.status == CUSTOMER_WAITING:
                    self.logger.debug("Customer {} received proposal from transport {}".format(self.agent.name,
                                                                                           transport_id))
                    await self.accept_transport(transport_id)
                    self.agent.status = CUSTOMER_ASSIGNED
                else:
                    await self.refuse_transport(transport_id)

            elif performative == CANCEL_PERFORMATIVE:
                if self.agent.transport_assigned == str(transport_id):
                    self.logger.warning("Customer {} received a CANCEL from Transport {}.".format(self.agent.name, transport_id))
                    self.agent.status = CUSTOMER_WAITING


################################################################
#                                                              #
#                       Secretary Strategy                     #
#                                                              #
################################################################
class AlwaysAnswerStrategyBehaviour(SecretaryStrategyBehaviour):
    """
    The default strategy for the Secretary agent. By default it answer the first message it receives.
    """
    async def run(self):
        msg = await self.receive(timeout=5)
        if msg:
            performative = msg.get_metadata("performative")
            agent_id = msg.sender
            request = msg.body
            if performative == REQUEST_PERFORMATIVE:
                self.logger.info("Secretary {} received message from customer/transport {}".format(self.agent.name,
                                                                                                   agent_id))
                if request in self.get("service_agents"):
                    await self.send_services(agent_id, msg.body)
                else:
                    await self.send_negative(agent_id)


################################################################
#                                                              #
#                        Station Strategy                      #
#                                                              #
################################################################
class ManageChargeSpacesBehaviour(StationStrategyBehaviour):
    """
    The default strategy for the Station agent. Manage electric charge spaces.
    """
    async def run(self):
        if not self.agent.registration:
            await self.send_registration()

        msg = await self.receive(timeout=5)

        if msg:
            performative = msg.get_metadata("performative")
            transport_id = msg.sender
            if performative == PROPOSE_PERFORMATIVE:
                if self.agent.get_status() == FREE_STATION:
                    self.logger.debug("Station {} received proposal from transport {}".format(self.agent.name,
                                                                                              transport_id))
                    await self.accept_transport(transport_id)
                else:  # self.agent.get_status() == BUSY_STATION
                    await self.refuse_transport(transport_id)
            elif performative == CANCEL_PERFORMATIVE:
                self.logger.warning("Station {} received a CANCEL from Transport {}.".format(self.agent.name, transport_id))
                self.agent.deassigning_place()
