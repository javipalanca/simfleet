import json

from loguru import logger

from .customer import CustomerStrategyBehaviour
from .fleetmanager import FleetManagerStrategyBehaviour
from .helpers import PathRequestException, distance_in_meters
from .protocol import REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, PROPOSE_PERFORMATIVE, \
    CANCEL_PERFORMATIVE, INFORM_PERFORMATIVE, QUERY_PROTOCOL, REQUEST_PROTOCOL
from .transport import TransportStrategyBehaviour
from .utils import TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL, CUSTOMER_WAITING, TRANSPORT_MOVING_TO_CUSTOMER, \
    CUSTOMER_ASSIGNED, TRANSPORT_MOVING_TO_STATION, \
    TRANSPORT_CHARGING, TRANSPORT_CHARGED, TRANSPORT_NEEDS_CHARGING, TRANSPORT_IN_STATION_PLACE


################################################################
#                                                              #
#                     FleetManager Strategy                    #
#                                                              #
################################################################
class DelegateRequestBehaviour(FleetManagerStrategyBehaviour):
    """
    The default strategy for the FleetManager agent. By default it delegates all requests to all transports.
    """

    async def run(self):
        if not self.agent.registration:
            await self.send_registration()

        msg = await self.receive(timeout=5)
        logger.debug("Manager received message: {}".format(msg))
        if msg:
            for transport in self.get_transport_agents().values():
                msg.to = str(transport["jid"])
                logger.debug("Manager sent request to transport {}".format(transport["name"]))
                await self.send(msg)


################################################################
#                                                              #
#                     Transport Strategy                       #
#                                                              #
################################################################
class AcceptAlwaysStrategyBehaviour(TransportStrategyBehaviour):
    """
    The default strategy for the Transport agent. By default it accepts every request it receives if available.
    """

    async def run(self):
        if self.agent.needs_charging():
            if self.agent.stations is None or len(self.agent.stations) < 1:
                logger.warning("Transport {} looking for a station.".format(self.agent.name))
                await self.send_get_stations()
            else:
                # choice of closest station
                station_positions = []
                for key in self.agent.stations.keys():
                    dic = self.agent.stations.get(key)
                    station_positions.append((dic['jid'], dic['position']))
                closest_station = min(station_positions,
                                      key=lambda x: distance_in_meters(x[1], self.agent.get_position()))
                # closest_station = min( station_positions, key = lambda x: request_route_to_server(x[1], self.agent.get_position(), "http://osrm.gti-ia.upv.es/")[1])

                # closest_station = min( list(self.agent.stations), key = lambda x: distance_in_meters( x['position'], self.agent.get_position() ) )
                logger.info("Closest station {}".format(closest_station))
                station = closest_station[0]

                # station = random.choice(list(self.agent.stations.keys()))
                position = self.agent.stations[station]["position"]
                logger.info("Transport {} selected station {}.".format(self.agent.name, station))

                try:
                    # transport moves to selected station
                    self.agent.status = TRANSPORT_MOVING_TO_STATION
                    await self.go_to_the_station(station, position)
                except PathRequestException:
                    logger.error("Transport {} could not get a path to station {}. Cancelling..."
                                 .format(self.agent.name, station))
                    self.agent.status = TRANSPORT_WAITING
                    await self.cancel_proposal(station)
                except Exception as e:
                    logger.error("Unexpected error in transport {}: {}".format(self.agent.name, e))
                    await self.cancel_proposal(station)
                    self.agent.status = TRANSPORT_WAITING

        msg = await self.receive(timeout=5)
        if not msg:
            return
        logger.debug("Transport received message: {}".format(msg))
        try:
            content = json.loads(msg.body)
        except TypeError:
            content = {}

        performative = msg.get_metadata("performative")
        protocol = msg.get_metadata("protocol")

        if protocol == QUERY_PROTOCOL:
            if performative == INFORM_PERFORMATIVE:
                self.agent.stations = content
                logger.info("Got list of current stations: {}".format(list(self.agent.stations.keys())))
            elif performative == CANCEL_PERFORMATIVE:
                logger.info("Cancellation of request for stations information.")

        elif protocol == REQUEST_PROTOCOL:
            logger.debug("Transport {} received request protocol from customer/station.".format(self.agent.name))

            if performative == REQUEST_PERFORMATIVE:
                if self.agent.status == TRANSPORT_WAITING:
                    if not self.has_enough_autonomy(content["origin"], content["dest"]):
                        await self.cancel_proposal(content["customer_id"])
                        self.agent.status = TRANSPORT_NEEDS_CHARGING
                    else:
                        await self.send_proposal(content["customer_id"], {})
                        self.agent.status = TRANSPORT_WAITING_FOR_APPROVAL

            elif performative == ACCEPT_PERFORMATIVE:
                if self.agent.status == TRANSPORT_WAITING_FOR_APPROVAL:
                    logger.debug("Transport {} got accept from {}".format(self.agent.name,
                                                                          content["customer_id"]))
                    try:
                        self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER
                        await self.pick_up_customer(content["customer_id"], content["origin"], content["dest"])
                    except PathRequestException:
                        logger.error("Transport {} could not get a path to customer {}. Cancelling..."
                                     .format(self.agent.name, content["customer_id"]))
                        self.agent.status = TRANSPORT_WAITING
                        await self.cancel_proposal(content["customer_id"])
                    except Exception as e:
                        logger.error("Unexpected error in transport {}: {}".format(self.agent.name, e))
                        await self.cancel_proposal(content["customer_id"])
                        self.agent.status = TRANSPORT_WAITING
                elif self.agent.status == TRANSPORT_IN_STATION_PLACE:
                    if content.get('station_id') is not None:
                        # debug
                        logger.info(
                            "++++++++++++++++++++++++++Transport {} received a message with ACCEPT_PERFORMATIVE from {}".format(
                                self.agent.name, content["station_id"]))
                        await self.charge_allowed()

                else:
                    await self.cancel_proposal(content["customer_id"])

            elif performative == REFUSE_PERFORMATIVE:
                logger.debug("Transport {} got refusal from customer/station".format(self.agent.name))
                self.agent.status = TRANSPORT_WAITING

            elif performative == INFORM_PERFORMATIVE:
                if self.agent.status == TRANSPORT_CHARGING:
                    if content["status"] == TRANSPORT_CHARGED:
                        self.agent.transport_charged()
                        await self.agent.drop_station()

            elif performative == CANCEL_PERFORMATIVE:
                logger.info("Cancellation of request for {} information".format(self.agent.fleet_type))


################################################################
#                                                              #
#                       Customer Strategy                      #
#                                                              #
################################################################
class AcceptFirstRequestBehaviour(CustomerStrategyBehaviour):
    """
    The default strategy for the Customer agent. By default it accepts the first proposal it receives.
    """

    async def run(self):
        if self.agent.fleetmanagers is None:
            await self.send_get_managers(self.agent.fleet_type)

            msg = await self.receive(timeout=5)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == INFORM_PERFORMATIVE:
                    self.agent.fleetmanagers = json.loads(msg.body)
                    return
                elif performative == CANCEL_PERFORMATIVE:
                    logger.info("Cancellation of request for {} information".format(self.agent.type_service))
                    return

        if self.agent.status == CUSTOMER_WAITING:
            await self.send_request(content={})

        msg = await self.receive(timeout=5)

        if msg:
            performative = msg.get_metadata("performative")
            transport_id = msg.sender
            if performative == PROPOSE_PERFORMATIVE:
                if self.agent.status == CUSTOMER_WAITING:
                    logger.debug(
                        "Customer {} received proposal from transport {}".format(self.agent.name, transport_id))
                    await self.accept_transport(transport_id)
                    self.agent.status = CUSTOMER_ASSIGNED
                else:
                    await self.refuse_transport(transport_id)

            elif performative == CANCEL_PERFORMATIVE:
                if self.agent.transport_assigned == str(transport_id):
                    logger.warning(
                        "Customer {} received a CANCEL from Transport {}.".format(self.agent.name, transport_id))
                    self.agent.status = CUSTOMER_WAITING
