# -*- coding: utf-8 -*-

"""Console script for taxi_simulator."""
import logging
import time
import click
import thread

from spade import spade_backend
from xmppd.xmppd import Server

from coordinator import CoordinatorAgent

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()


@click.command()
def main(args=None):
    """Console script for taxi_simulator."""
    s = Server(cfgfile="xmppd.xml", cmd_options={'enable_debug': [],
                                                 'enable_psyco': False})
    thread.start_new_thread(s.run, tuple())
    logger.info("XMPP server running.")
    platform = spade_backend.SpadeBackend(s, "spade.xml")
    platform.start()
    logger.info("Running SPADE platform.")

    coordinator_agent = CoordinatorAgent("coordinator@127.0.0.1", password="kakatua", debug=[])
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
    s.shutdown("")


if __name__ == "__main__":
    main()
