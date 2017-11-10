# -*- coding: utf-8 -*-

"""Console script for taxi_simulator."""
import logging
import threading
import time
import click
import thread
import sys
import os
import cPickle as pickle

from spade import spade_backend
from xmppd.xmppd import Server

from coordinator import CoordinatorAgent

logger = logging.getLogger()


@click.command()
@click.option('--taxi', default="taxi_simulator.strategies.AcceptAlwaysStrategyBehaviour",
              help='Taxi strategy class.')
@click.option('--passenger', default="taxi_simulator.strategies.AcceptFirstRequestTaxiBehaviour",
              help='Passenger strategy class.')
@click.option('--coordinator', default="taxi_simulator.strategies.DelegateRequestTaxiBehaviour",
              help='Coordinator strategy class.')
@click.option('--debug', default=False, is_flag=True,
              help='Show verbose debug.')
@click.option('--port', default=9000, help="Web interface port.")
@click.option('--name', default="coordinator", help="Coordinator agent name.")
@click.option('--passwd', default="coordinator_passwd", help="Coordinator agent password.")
def main(taxi, passenger, coordinator, debug, port, name, passwd):
    """Console script for taxi_simulator."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # generate config
    if not os.path.exists("spade.xml") or not os.path.exists("xmppd.xml"):
        os.system("configure.py 127.0.0.1")

    # reset user_db
    with open("user_db.xml", 'w') as f:
        pickle.dump({"127.0.0.1": {}}, f)

    s = Server(cfgfile="xmppd.xml", cmd_options={'enable_debug': [],
                                                 'enable_psyco': False})
    thread.start_new_thread(s.run, tuple())
    logger.info("XMPP server running.")
    platform = spade_backend.SpadeBackend(s, "spade.xml")
    platform.start()
    logger.info("Running SPADE platform.")

    coordinator_agent = CoordinatorAgent(name+"@127.0.0.1", password=passwd, debug=[], http_port=port)
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
    s.shutdown("")
    sys.exit(0)


if __name__ == "__main__":
    main()
