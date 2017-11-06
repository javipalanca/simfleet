# -*- coding: utf-8 -*-

"""Console script for taxi_simulator."""
import logging
import time
import click
import thread

from spade import spade_backend
from xmppd.xmppd import Server

from simulator import SimulatorAgent

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()


@click.command()
def main(args=None):
    """Console script for taxi_simulator."""
    # click.echo("Replace this message by putting your code into "
    #           "taxi_simulator.cli.main")
    # click.echo("See click documentation at http://click.pocoo.org/")

    s = Server(cfgfile="xmppd.xml", cmd_options={'enable_debug': [],
                                                 'enable_psyco': False})
    thread.start_new_thread(s.run, tuple())
    logger.info("XMPP server running.")
    platform = spade_backend.SpadeBackend(s, "spade.xml")
    platform.start()
    logger.info("Running SPADE platform.")

    simulator_agent = SimulatorAgent("simulator@127.0.0.1", password="kakatua", debug=[])
    simulator_agent.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\nTerminating...")
            simulator_agent.stop_agents()
            simulator_agent.stop()
            platform.shutdown()
            s.shutdown("")
            break


if __name__ == "__main__":
    main()
