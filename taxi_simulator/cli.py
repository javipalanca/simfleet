# -*- coding: utf-8 -*-

"""Console script for taxi_simulator."""
import logging
import threading
import time
import click
import thread
import sys

from spade import spade_backend
from tqdm import tqdm
from xmppd.xmppd import Server

from coordinator import CoordinatorAgent

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()


@click.command()
@click.option('--taxi', default="strategies.AcceptAlwaysStrategyBehaviour",
              help='Taxi strategy class.')
@click.option('--passenger', default="strategies.AcceptFirstRequestTaxiBehaviour",
              help='Passenger strategy class.')
@click.option('--coordinator', default="strategies.DelegateRequestTaxiBehaviour",
              help='Coordinator strategy class.')
def main(taxi, passenger, coordinator):
    """Console script for taxi_simulator."""
    s = Server(cfgfile="xmppd.xml", cmd_options={'enable_debug': [],
                                                 'enable_psyco': False})
    thread.start_new_thread(s.run, tuple())
    logger.info("XMPP server running.")
    platform = spade_backend.SpadeBackend(s, "spade.xml")
    platform.start()
    logger.info("Running SPADE platform.")

    coordinator_agent = CoordinatorAgent("coordinator@127.0.0.1", password="kakatua", debug=[])
    coordinator_agent.set_strategies(coordinator, taxi, passenger)
    coordinator_agent.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    click.echo("\nTerminating...")
    coordinator_agent.stop_agents()
    coordinator_agent.stop()
    platform.shutdown()

    with tqdm(total=threading.active_count() - 48) as pbar:
        while threading.active_count() > 48:
            pbar.update(threading.active_count() - 48)
            time.sleep(1)

    s.shutdown("")
    sys.exit(0)


if __name__ == "__main__":
    main()
