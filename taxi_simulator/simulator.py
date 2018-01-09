import logging

import pandas as pd
from tabulate import tabulate
import thread
import os

import pickle

from multiprocessing import Process
from multiprocessing.queues import SimpleQueue

from spade import spade_backend
from xmppd.xmppd import Server
from flask import Flask

from utils import crossdomain
from coordinator import CoordinatorAgent
from scenario import Scenario

logger = logging.getLogger()


class SimulationConfig(object):
    def __init__(self):
        self.simulation_name = None
        self.max_time = None
        self.taxi_strategy = None
        self.passenger_strategy = None
        self.coordinator_strategy = None
        self.scenario = None
        self.num_taxis = None
        self.num_passengers = None
        self.http_port = None
        self.coordinator_name = None
        self.coordinator_password = None
        self.backend_port = None
        self.verbose = None


class Simulator(object):
    def __init__(self, config):
        self.config = config
        self.pretty_name = "({})".format(self.config.simulation_name) if self.config.simulation_name else ""
        self.verbose = self.config.verbose

        self.coordinator_agent = None

        self.command_queue = SimpleQueue()

        # generate config
        if not os.path.exists("spade.xml") or not os.path.exists("xmppd.xml"):
            os.system("configure.py 127.0.0.1")

        # reset user_db
        with open("user_db.xml", 'w') as f:
            pickle.dump({"127.0.0.1": {}}, f)

        debug_level = ['always'] if self.config.verbose > 2 else []
        self.xmpp_server = Server(cfgfile="xmppd.xml", cmd_options={'enable_debug': debug_level,
                                                                    'enable_psyco': False})

        logger.info("Starting Taxi Simulator {}".format(self.pretty_name))
        thread.start_new_thread(self.xmpp_server.run, tuple())
        logger.debug("XMPP server running.")
        self.platform = spade_backend.SpadeBackend(self.xmpp_server, "spade.xml")
        self.platform.start()
        logger.debug("Running SPADE platform.")

        debug_level = ['always'] if self.verbose > 1 else []
        self.coordinator_agent = CoordinatorAgent(config.coordinator_name + "@127.0.0.1",
                                                  password=config.coordinator_password,
                                                  debug=debug_level,
                                                  http_port=config.http_port,
                                                  backend_port=config.backend_port,
                                                  debug_level=debug_level)
        self.coordinator_agent.set_strategies(config.coordinator_strategy,
                                              config.taxi_strategy,
                                              config.passenger_strategy)
        self.coordinator_agent.start()

        logger.info("Creating {} taxis and {} passengers.".format(config.num_taxis, config.num_passengers))
        Scenario.create_agents_batch("taxi", config.num_taxis, self.coordinator_agent)
        Scenario.create_agents_batch("passenger", config.num_passengers, self.coordinator_agent)

        if config.scenario:
            scenario = Scenario(config.scenario, debug_level)
            for agent in scenario.taxis:
                self.coordinator_agent.add_taxi(agent)
                agent.start()
            for agent in scenario.passengers:
                self.coordinator_agent.add_passenger(agent)
                agent.start()

        self.web_backend_process = Process(None, _worker, "async web interface listener",
                                           [self.command_queue, "127.0.0.1",
                                            config.backend_port, False])
        self.web_backend_process.start()

    def is_simulation_finished(self):
        if self.config.max_time is None:
            return False
        return self.time_is_out() or self.coordinator_agent.is_simulation_finished()

    def time_is_out(self):
        return self.coordinator_agent.get_simulation_time() > self.config.max_time

    def run(self):
        self.coordinator_agent.run_simulation()

    def process_queue(self):
        if not self.command_queue.empty():
            ntaxis, npassengers = self.command_queue.get()
            logger.info("Creating {} taxis and {} passengers.".format(ntaxis, npassengers))
            Scenario.create_agents_batch("taxi", ntaxis, self.coordinator_agent)
            Scenario.create_agents_batch("passenger", npassengers, self.coordinator_agent)

    def stop(self):
        simulation_time = self.coordinator_agent.get_simulation_time()

        logger.info("\nTerminating... ({0:.1f} seconds elapsed)".format(simulation_time))

        self.web_backend_process.terminate()

        passenger_df = self.coordinator_agent.get_passenger_stats()
        taxi_df = self.coordinator_agent.get_taxi_stats()
        stats = self.coordinator_agent.get_stats()
        df_avg = pd.DataFrame.from_dict({"Avg Waiting Time": [stats["waiting"]],
                                         "Avg Total Time": [stats["totaltime"]],
                                         "Simulation Finished": [stats["finished"]]
                                         })
        columns = ["Avg Waiting Time", "Avg Total Time", "Simulation Finished"]
        if self.config.simulation_name:
            df_avg["Simulation Name"] = self.config.simulation_name
            columns = ["Simulation Name"] + columns
        df_avg = df_avg[columns]

        self.coordinator_agent.stop_agents()

        print("Simulation Results")
        print(tabulate(df_avg, headers="keys", showindex=False, tablefmt="fancy_grid"))
        print("Passenger stats")
        print(tabulate(passenger_df, headers="keys", showindex=False, tablefmt="fancy_grid"))
        print("Taxi stats")
        taxi_df = taxi_df[["name", "assignments", "distance", "status"]]
        print(tabulate(taxi_df, headers="keys", showindex=False, tablefmt="fancy_grid"))

        self.coordinator_agent.stop()
        self.platform.shutdown()
        self.xmpp_server.shutdown("")


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
