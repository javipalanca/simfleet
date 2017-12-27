# -*- coding: utf-8 -*-

"""Console script for taxi_simulator."""
import json
import click
import logging
import thread
import sys
import os
import time
import cPickle as pickle

from flask import Flask
from multiprocessing import Process
from multiprocessing.queues import SimpleQueue

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
@click.option('--scenario', help="Filename of JSON file with initial scenario description.")
@click.option('--name', default="coordinator",
              help="Coordinator agent name (default: coordinator).")
@click.option('--passwd', default="coordinator_passwd",
              help="Coordinator agent password (default: coordinator_passwd).")
@click.option('-bp', '--backend-port', default=5000, help="Backend port (default: 5000).")
@click.option('-v', '--verbose', count=True,
              help="Show verbose debug level: -v level 1, -vv level 2, -vvv level 3, -vvvv level 4")
def main(taxi, passenger, coordinator, port, num_taxis, num_passengers, scenario, name, passwd, backend_port, verbose):
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
    create_agents_batch("taxi", num_taxis, coordinator_agent)
    create_agents_batch("passenger", num_passengers, coordinator_agent)

    if scenario:
        with open(scenario, 'r') as f:
            logger.info("Loading scenario {}".format(scenario))
            scenario = json.load(f)
            for taxi in scenario["taxis"]:
                agent = create_agent(TaxiAgent, taxi["name"], taxi["password"], taxi["position"], None, debug_level)
                agent.set_speed(taxi["speed"])
                coordinator_agent.taxi_agents[taxi["name"]] = agent
                agent.start()
            for passenger in scenario["passengers"]:
                agent = create_agent(PassengerAgent, passenger["name"], passenger["password"], passenger["position"],
                                     passenger["dest"], debug_level)
                coordinator_agent.passenger_agents[passenger["name"]] = agent
                agent.start()

    command_queue = SimpleQueue()
    web_backend_process = Process(None, _worker, "async web interface listener", [command_queue, "127.0.0.1",
                                                                                  backend_port, False])
    web_backend_process.start()

    while True:
        try:
            time.sleep(1)
            if not command_queue.empty():
                ntaxis, npassengers = command_queue.get()
                logger.info("Creating {} taxis and {} passengers.".format(ntaxis, npassengers))
                create_agents_batch("taxi", ntaxis, coordinator_agent)
                create_agents_batch("passenger", npassengers, coordinator_agent)
        except KeyboardInterrupt:
            break

    click.echo("\nTerminating...")

    web_backend_process.terminate()

    coordinator_agent.stop_agents()
    coordinator_agent.stop()
    platform.shutdown()
    s.shutdown("")
    sys.exit(0)


def _worker(command_queue, host, port, debug):
    FlaskBackend(command_queue, host, port, debug)


class FlaskBackend(object):
    def __init__(self, command_queue, host='0.0.0.0', port=5000, debug=False):
        self.command_queue = command_queue
        self.app = Flask('FlaskBackend')
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.app.add_url_rule("/generate/taxis/<int:ntaxis>/passengers/<int:npassengers>", "generate", self.generate)
        self.app.run(host=host, port=port, debug=debug, use_reloader=debug)

    @crossdomain(origin='*')
    def generate(self, ntaxis, npassengers):
        self.command_queue.put((ntaxis, npassengers))
        return ""


def create_agents_batch(type_, number, coordinator):
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
            agent = create_agent(cls, name, password, position, None, coordinator.debug_level)
            store[name] = agent
            agent.start()
            if coordinator.simulation_running:
                agent.add_strategy(strategy)
            logger.debug("Created {} {} at position {}".format(type_, name, position))


def create_agent(cls, name, password, position, target, debug_level):
    jid = name + "@127.0.0.1"
    agent = cls(jid, password, debug=debug_level)
    agent.set_id(name)
    agent.set_position(position)
    if target:
        agent.set_target_position(target)
    return agent


if __name__ == "__main__":
    main()
