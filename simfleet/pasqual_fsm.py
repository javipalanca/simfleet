import asyncio
import json

from loguru import logger
from spade.behaviour import State, FSMBehaviour

from simfleet.helpers import PathRequestException, distance_in_meters
from simfleet.protocol import REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, REQUEST_PROTOCOL, \
    INFORM_PERFORMATIVE
from simfleet.transport import TransportStrategyBehaviour
from simfleet.utils import TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_MOVING_TO_CUSTOMER, \
    TRANSPORT_NEEDS_CHARGING, TRANSPORT_MOVING_TO_STATION, TRANSPORT_IN_STATION_PLACE, TRANSPORT_CHARGING, \
    TRANSPORT_CHARGED


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
            if not self.has_enough_autonomy(content["origin"], content["dest"]):
                await self.cancel_proposal(content["customer_id"])
                # self.agent.status = TRANSPORT_NEEDS_CHARGING
                self.set_next_state(TRANSPORT_NEEDS_CHARGING)
                return
            else:
                await self.send_proposal(content["passenger_id"], {})
                self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
                return
        else:
            self.set_next_state(TRANSPORT_WAITING)
            return


class TransportNeedsChargingState(TransportStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_NEEDS_CHARGING
        if self.agent.stations is None or len(self.agent.stations) < 1:
            logger.warning("Transport {} looking for a station.".format(self.agent.name))
            self.set_next_state()
            await self.send_get_stations()

    async def run(self):
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
        self.agent.current_station_dest = (station, self.agent.stations[station]["position"])
        logger.info("Transport {} selected station {}.".format(self.agent.name, station))
        self.set_next_state(TRANSPORT_MOVING_TO_STATION)
        return


class TransportMovingToStationState(TransportStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_STATION

    async def run(self):
        try:
            station, position = self.agent.current_station_dest
            # substituir per event arrived_to_station?
            await self.go_to_the_station(station, position)
            self.set_next_state(TRANSPORT_IN_STATION_PLACE)  # ???

        except PathRequestException:
            logger.error("Transport {} could not get a path to station {}. Cancelling..."
                         .format(self.agent.name, station))
            await self.cancel_proposal(station)
            self.set_next_state(TRANSPORT_WAITING)
            return
        except Exception as e:
            logger.error("Unexpected error in transport {}: {}".format(self.agent.name, e))
            self.set_next_state(TRANSPORT_WAITING)
            return


class TransportWaitingForApprovalState(TransportStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_WAITING_FOR_APPROVAL

    async def run(self):
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
            return
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")
        if performative == ACCEPT_PERFORMATIVE:
            try:
                logger.debug("Transport {} got accept from {}".format(self.agent.name,
                                                                      content["customer_id"]))
                await self.pick_up_customer(content["customer_id"], content["origin"], content["dest"])
                self.set_next_state(TRANSPORT_MOVING_TO_CUSTOMER)
                return
            except PathRequestException:
                logger.error("Transport {} could not get a path to customer {}. Cancelling..."
                             .format(self.agent.name, content["customer_id"]))
                await self.cancel_proposal(content["customer_id"])
                self.set_next_state(TRANSPORT_WAITING)
                return
            except Exception as e:
                logger.error("Unexpected error in transport {}: {}".format(self.agent.name, e))
                await self.cancel_proposal(content["customer_id"])
                self.set_next_state(TRANSPORT_WAITING)
                return

        elif performative == REFUSE_PERFORMATIVE:
            logger.debug("Transport {} got refusal from customer/station".format(self.agent.name))
            self.set_next_state(TRANSPORT_WAITING)
            return

        else:
            self.set_next_state(TRANSPORT_WAITING_FOR_APPROVAL)
            return


# SENSE CANVIS

# Idees:
#   + El TransportMovingState pot englobar el TRANSPORT_MOVING_TO_CUSTOMER y el TRANSPORT_MOVING_TO_STATION
#     ja que els dos utilitzen el move_to(), encara que un dels movimenta acaba amb arrived_to_destination
#     y l'altre acaba amb arrived_to_station

passenger_in_transport_event = asyncio.Event()


def passenger_in_transport_callback(old, new):
    if not passenger_in_transport_event.is_set() and new is None:
        passenger_in_transport_event.set()


class TransportMovingToCustomerState(TransportStrategyBehaviour, State):

    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_MOVING_TO_CUSTOMER

    async def run(self):
        passenger_in_transport_event.clear()
        self.agent.watch_value("passenger_in_transport", passenger_in_transport_callback)
        await passenger_in_transport_event.wait()
        logger.info("Transport is free again.")
        return self.set_next_state(TRANSPORT_WAITING)

# END SENSE CANVIS


class TransportInStationState(TransportStrategyBehaviour, State):
    # car arrives to the station and waits in queue until receiving confirmation
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_IN_STATION_PLACE

    async def run(self):
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_IN_STATION_PLACE)
            return
        content = json.loads(msg.body)
        performative = msg.get_metadata("performative")
        if performative == ACCEPT_PERFORMATIVE:
            if content.get('station_id') is not None:
                # debug
                logger.info(
                    "++++++++++++++++++++++++++Transport {} received a message with ACCEPT_PERFORMATIVE from {}".format(
                        self.agent.name, content["station_id"]))

                # CANVIAR PER EVENT?

                await self.charge_allowed()
                self.set_next_state(TRANSPORT_CHARGING)
                return

        else:
            # if the message I receive is not an ACCEPT, I keep waiting in the queue
            self.set_next_state(TRANSPORT_IN_STATION_PLACE)
            return



class TransportChargingState(TransportStrategyBehaviour, State):
    # car charges in a station
    async def on_start(self):
        await super().on_start()
        self.agent.status = TRANSPORT_CHARGING # this change is already performed in function begin_charging() of class Transport

    async def run(self):
        # awaiy "transport_charged" message
        msg = await self.receive(timeout=60)
        if not msg:
            self.set_next_state(TRANSPORT_CHARGING)
            return
        content = json.loads(msg.body)
        protocol = msg.get_metadata("protocol")
        performative = msg.get_metadata("performative")
        if protocol == REQUEST_PROTOCOL and performative == INFORM_PERFORMATIVE:
            if content["status"] == TRANSPORT_CHARGED:
                self.agent.transport_charged()
                await self.agent.drop_station()
                # canviar per un event?
                self.set_next_state(TRANSPORT_WAITING)
                return


class FSMTransportStrategyBehaviour(FSMBehaviour):
    def setup(self):
        # Create states
        self.add_state(TRANSPORT_WAITING, TransportWaitingState(), initial=True)
        self.add_state(TRANSPORT_NEEDS_CHARGING, TransportNeedsChargingState())
        self.add_state(TRANSPORT_WAITING_FOR_APPROVAL, TransportWaitingForApprovalState())
        self.add_state(TRANSPORT_MOVING_TO_CUSTOMER, TransportMovingToCustomerState())
        self.add_state(TRANSPORT_MOVING_TO_STATION, TransportMovingToStationState())
        self.add_state(TRANSPORT_IN_STATION_PLACE, TransportInStationState())
        self.add_state(TRANSPORT_CHARGING, TransportChargingState())

        # Create transitions
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_WAITING)                       # waiting for messages
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_WAITING_FOR_APPROVAL)          # accepted by customer
        self.add_transition(TRANSPORT_WAITING, TRANSPORT_NEEDS_CHARGING)                # not enough charge

        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_WAITING_FOR_APPROVAL) # waiting for approval message
        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_WAITING)              # transport refused
        self.add_transition(TRANSPORT_WAITING_FOR_APPROVAL, TRANSPORT_MOVING_TO_CUSTOMER)   # going to pick up customer

        self.add_transition(TRANSPORT_NEEDS_CHARGING, TRANSPORT_MOVING_TO_STATION)      # going to station
        self.add_transition(TRANSPORT_MOVING_TO_STATION, TRANSPORT_IN_STATION_PLACE)    # arrive to station
        self.add_transition(TRANSPORT_MOVING_TO_STATION, TRANSPORT_MOVING_TO_STATION)   # ??
        self.add_transition(TRANSPORT_IN_STATION_PLACE, TRANSPORT_IN_STATION_PLACE)     # waiting in station queue
        self.add_transition(TRANSPORT_IN_STATION_PLACE, TRANSPORT_CHARGING)             # begin charging
        self.add_transition(TRANSPORT_CHARGING, TRANSPORT_WAITING)                      # restart strategy

        self.add_transition(TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_WAITING)            # picked up customer or arrived to destination ??
