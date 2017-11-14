# -*- coding: utf-8 -*-

"""Console script for taxi_simulator."""
import click
import logging
import thread
import sys
import os
import cPickle as pickle

from flask import Flask

from spade import spade_backend
from xmppd.xmppd import Server

from coordinator import CoordinatorAgent
from passenger import PassengerAgent
from taxi import TaxiAgent
from utils import random_position, crossdomain

logger = logging.getLogger()


@click.command()
@click.option('-t', '--taxi', default="taxi_simulator.strategies.AcceptAlwaysStrategyBehaviour",
              help='Taxi strategy class (default: AcceptAlwaysStrategyBehaviour).')
@click.option('-p', '--passenger', default="taxi_simulator.strategies.AcceptFirstRequestTaxiBehaviour",
              help='Passenger strategy class (default: AcceptFirstRequestTaxiBehaviour).')
@click.option('-c', '--coordinator', default="taxi_simulator.strategies.DelegateRequestTaxiBehaviour",
              help='Coordinator strategy class (default: DelegateRequestTaxiBehaviour).')
@click.option('--port', default=9000, help="Web interface port (default: 9000).")
@click.option('-nt', '--num-taxis', default=0, help="Number of initial taxis to create (default: 0).")
@click.option('-np', '--num-passengers', default=0, help="Number of initial passengers to create (default: 0).")
@click.option('--name', default="coordinator",
              help="Coordinator agent name (default: coordinator).")
@click.option('--passwd', default="coordinator_passwd",
              help="Coordinator agent password (default: coordinator_passwd).")
@click.option('-bp', '--backend-port', default=5000, help="Backend port (default: 5000).")
@click.option('-v', '--verbose', count=True,
              help='Show verbose debug.')
def main(taxi, passenger, coordinator, port, num_taxis, num_passengers, name, passwd, backend_port, verbose):
    """Console script for taxi_simulator."""
    if verbose > 0:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # generate config
    if not os.path.exists("spade.xml") or not os.path.exists("xmppd.xml"):
        os.system("configure.py 127.0.0.1")

    # reset user_db
    with open("user_db.xml", 'w') as f:
        pickle.dump({"127.0.0.1": {}}, f)

    debug_level = ['always'] if verbose > 2 else []
    s = Server(cfgfile="xmppd.xml", cmd_options={'enable_debug': debug_level,
                                                 'enable_psyco': False})
    thread.start_new_thread(s.run, tuple())
    logger.info("XMPP server running.")
    platform = spade_backend.SpadeBackend(s, "spade.xml")
    platform.start()
    logger.info("Running SPADE platform.")

    debug_level = ['always'] if verbose > 1 else []
    coordinator_agent = CoordinatorAgent(name + "@127.0.0.1", password=passwd, debug=debug_level,
                                         http_port=port, backend_port=backend_port, debug_level=debug_level)
    coordinator_agent.set_strategies(coordinator, taxi, passenger)
    coordinator_agent.start()

    logger.info("Creating {} taxis and {} passengers.".format(num_taxis, num_passengers))
    create_agent("taxi", num_taxis, coordinator_agent)
    create_agent("passenger", num_passengers, coordinator_agent)

    app = Flask(__name__)

    @app.route("/generate/taxis/<int:ntaxis>/passengers/<int:npassengers>")
    @crossdomain(origin='*')
    def generate(ntaxis, npassengers):
        logger.info("Creating {} taxis and {} passengers.".format(ntaxis, npassengers))
        create_agent("taxi", ntaxis, coordinator_agent)
        create_agent("passenger", npassengers, coordinator_agent)
        return ""

    app.run(host="127.0.0.1", port=backend_port)

    click.echo("\nTerminating...")

    coordinator_agent.stop_agents()
    coordinator_agent.stop()
    platform.shutdown()
    s.shutdown("")
    sys.exit(0)


def create_agent(type_, number, coordinator):
    if type_ == "taxi":
        cls = TaxiAgent
        store = coordinator.taxi_agents
        strategy = coordinator.taxi_strategy
    else:  # type_ == "passenger":
        cls = PassengerAgent
        store = coordinator.passenger_agents
        strategy = coordinator.passenger_strategy
    for _ in range(number):
        with coordinator.lock:
            if coordinator.kill_simulator.isSet():
                break
            position = random_position()
            name = coordinator.faker.user_name()
            password = coordinator.faker.password()
            jid = name + "@127.0.0.1"
            agent = cls(jid, password, debug=coordinator.debug_level)
            agent.set_id(name)
            agent.set_position(position)
            store[name] = agent
            agent.start()
            if coordinator.simulation_running:
                agent.add_strategy(strategy)
            logger.debug("Created {} {} at position {}".format(type_, name, position))


if __name__ == "__main__":
    main()
