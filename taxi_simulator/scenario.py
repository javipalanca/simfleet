import json
import logging

import faker

from passenger import PassengerAgent
from taxi import TaxiAgent
from utils import random_position

logger = logging.getLogger()

faker_factory = faker.Factory.create()


class Scenario(object):
    def __init__(self, filename, debug_level=None):
        if debug_level is None:
            debug_level = []
        self.taxis = []
        self.passengers = []
        with open(filename, 'r') as f:
            logger.info("Loading scenario {}".format(filename))
            scenario = json.load(f)
            for taxi in scenario["taxis"]:
                password = taxi["password"] if "password" in taxi else faker_factory.password()
                agent = self.create_agent(TaxiAgent, taxi["name"], password, taxi["position"], None, debug_level)
                agent.set_speed(taxi["speed"])
                self.taxis.append(agent)

            for passenger in scenario["passengers"]:
                agent = self.create_agent(PassengerAgent, passenger["name"], passenger["password"],
                                          passenger["position"],
                                          passenger["dest"], debug_level)
                self.passengers.append(agent)

    @staticmethod
    def create_agent(cls, name, password, position, target, debug_level):
        jid = name + "@127.0.0.1"
        agent = cls(jid, password, debug=debug_level)
        agent.set_id(name)
        agent.set_position(position)
        if target:
            agent.set_target_position(target)
        return agent

    @classmethod
    def create_agents_batch(cls, type_, number, coordinator):
        if type_ == "taxi":
            _cls = TaxiAgent
            store = coordinator.taxi_agents
            strategy = coordinator.taxi_strategy
        else:  # type_ == "passenger":
            _cls = PassengerAgent
            store = coordinator.passenger_agents
            strategy = coordinator.passenger_strategy
        for _ in range(number):
            with coordinator.lock:
                if coordinator.kill_simulator.isSet():
                    break
                position = random_position()
                name = faker_factory.user_name()
                password = faker_factory.password()
                agent = cls.create_agent(_cls, name, password, position, None, coordinator.debug_level)
                store[name] = agent
                agent.start()
                if coordinator.simulation_running:
                    agent.add_strategy(strategy)
                logger.debug("Created {} {} at position {}".format(type_, name, position))
