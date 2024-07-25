import json
import time
from asyncio import CancelledError

from loguru import logger

from simfleet.common.extensions.customers.models.taxicustomer import TaxiCustomerStrategyBehaviour
from simfleet.communications.protocol import (
    QUERY_PROTOCOL,
    INFORM_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    PROPOSE_PERFORMATIVE
)
from simfleet.utils.utils_old import (
    CUSTOMER_WAITING,
    CUSTOMER_ASSIGNED,
    TRANSPORT_MOVING_TO_CUSTOMER,
    TRANSPORT_IN_CUSTOMER_PLACE,
    CUSTOMER_IN_TRANSPORT,
    CUSTOMER_IN_DEST
)


################################################################
#                                                              #
#                       Customer Strategy                      #
#                                                              #
################################################################

#class AcceptFirstRequestBehaviour(CustomerStrategyBehaviour):
class AcceptFirstRequestBehaviour(TaxiCustomerStrategyBehaviour):
    """
    The default strategy for the Customer agent. By default it accepts the first proposal it receives.
    """

    async def run(self):

        if self.agent.fleetmanagers is None:

            self.agent.fleetmanagers = await self.agent.get_list_agent_position(self.agent.fleet_type, self.agent.fleetmanagers)

            return

            #await self.send_get_managers(self.agent.fleet_type)

            # msg = await self.receive(timeout=300)
            # if msg:
            #     protocol = msg.get_metadata("protocol")
            #     if protocol == QUERY_PROTOCOL:
            #         performative = msg.get_metadata("performative")
            #         if performative == INFORM_PERFORMATIVE:
            #             self.agent.fleetmanagers = json.loads(msg.body)
            #             logger.info(
            #                 "{} got fleet managers {}".format(
            #                     self.agent.name, self.agent.fleetmanagers
            #                 )
            #             )
            #         elif performative == CANCEL_PERFORMATIVE:
            #             logger.info(
            #                 "{} got cancellation of request for {} information".format(
            #                     self.agent.name, self.agent.fleet_type
            #                 )
            #             )
            # return


        if self.agent.status == CUSTOMER_WAITING:
            await self.send_request(content={})

        try:
            msg = await self.receive(timeout=5)

            if msg:
                performative = msg.get_metadata("performative")
                transport_id = msg.sender
                content = json.loads(msg.body)
                logger.debug("Customer {} informed of: {}".format(self.agent.name, content))

                if performative == PROPOSE_PERFORMATIVE:
                    if self.agent.status == CUSTOMER_WAITING:
                        logger.debug(
                            "Customer {} received proposal from transport {}".format(
                                self.agent.name, transport_id
                            )
                        )
                        await self.accept_transport(transport_id)
                        self.agent.status = CUSTOMER_ASSIGNED
                    else:
                        await self.refuse_transport(transport_id)

                elif performative == CANCEL_PERFORMATIVE:
                    if self.agent.transport_assigned == str(transport_id):
                        logger.warning(
                            "Customer {} received a CANCEL from Transport {}.".format(
                                self.agent.name, transport_id
                            )
                        )
                        self.agent.status = CUSTOMER_WAITING

                elif performative == INFORM_PERFORMATIVE:
                    if "status" in content:
                        status = content["status"]
                        # if status != CUSTOMER_LOCATION:
                        #    logger.debug(
                        #        "Customer {} informed of status: {}".format(
                        #            self.agent.name, status_to_str(status)
                        #        )
                        #    )
                        if status == TRANSPORT_MOVING_TO_CUSTOMER:
                            logger.info(
                                "Customer {} waiting for transport.".format(self.agent.name)
                            )
                            self.agent.waiting_for_pickup_time = time.time()
                        elif status == TRANSPORT_IN_CUSTOMER_PLACE:
                            self.agent.status = CUSTOMER_IN_TRANSPORT
                            logger.info("Customer {} in transport.".format(self.agent.name))
                            self.agent.pickup_time = time.time()
                            await self.inform_transport(transport_id, CUSTOMER_IN_TRANSPORT)
                        elif status == CUSTOMER_IN_DEST:
                            self.agent.status = CUSTOMER_IN_DEST
                            self.agent.end_time = time.time()
                            await self.inform_transport(transport_id, CUSTOMER_IN_DEST)
                            logger.info(
                                "Customer {} arrived to destination after {} seconds.".format(
                                    self.agent.name, self.agent.total_time()
                                )
                            )
        #TravelBehaviour - customer.py
        # try:
            # msg = await self.receive(timeout=5)
            # if not msg:
            #    return
            # content = json.loads(msg.body)
            # logger.debug("Customer {} informed of: {}".format(self.agent.name, content))
            # if "status" in content:
            #    status = content["status"]
            #    if status != CUSTOMER_LOCATION:
            #        logger.debug(
            #            "Customer {} informed of status: {}".format(
            #                self.agent.name, status_to_str(status)
            #            )
            #        )
            #    if status == TRANSPORT_MOVING_TO_CUSTOMER:
            #        logger.info(
            #            "Customer {} waiting for transport.".format(self.agent.name)
            #        )
            #        self.agent.waiting_for_pickup_time = time.time()
            #    elif status == TRANSPORT_IN_CUSTOMER_PLACE:
            #        self.agent.status = CUSTOMER_IN_TRANSPORT
            #        logger.info("Customer {} in transport.".format(self.agent.name))
            #        self.agent.pickup_time = time.time()
            #    elif status == CUSTOMER_IN_DEST:
            #        self.agent.status = CUSTOMER_IN_DEST
            #        self.agent.end_time = time.time()
            #        logger.info(
            #            "Customer {} arrived to destination after {} seconds.".format(
            #                self.agent.name, self.agent.total_time()
            #            )
            #        )
            # elif status == CUSTOMER_LOCATION:
            #    coords = content["location"]
            #    self.agent.set_position(coords)
        except CancelledError:
            logger.debug("Cancelling async tasks...")

        except Exception as e:
            logger.error(
                "EXCEPTION in AcceptFirstRequestBehaviour of Customer {}: {}".format(
                    self.agent.name, e
                )
            )
