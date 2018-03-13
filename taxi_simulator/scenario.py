import json
import logging

import faker

from passenger import PassengerAgent
from taxi import TaxiAgent
from helpers import random_position

logger = logging.getLogger()

faker_factory = faker.Factory.create()


class Scenario(object):
    """
    A scenario object reads a file with a JSON representation of a scenario and is used to create the participant agents.
    """
    def __init__(self, filename, debug_level=None):
        """
        The Scenario constructor reads the JSON file and creates the defined agents found in that file.
        Args:
            filename (str): the name of the scenario file
            debug_level: level of debug (None or 'always')
        """
        if debug_level is None:
            debug_level = []
        self.taxis = []
        self.passengers = []
        with open(filename, 'r') as f:
            logger.info("Loading scenario {}".format(filename))
            scenario = json.load(f)
            for taxi in scenario["taxis"]:
                password = taxi["password"] if "password" in taxi else faker_factory.password()
                agent = Scenario.create_agent(TaxiAgent, taxi["name"], password, taxi["position"], None, debug_level)
                if "speed" in taxi.keys():
                    agent.set_speed(taxi["speed"])
                self.taxis.append(agent)

            for passenger in scenario["passengers"]:
                password = passenger["password"] if "password" in passenger else faker_factory.password()
                agent = Scenario.create_agent(PassengerAgent, passenger["name"], password,
                                          passenger["position"],
                                          passenger["dest"], debug_level)
                self.passengers.append(agent)

    @staticmethod
    def create_agent(cls, name, password, position, target, debug_level):
        """
        Create an agent of type ``cls``.

        Args:
            cls (class): class of the agent
            name (str): name of the agent
            password (str): password of the agent
            position (list): initial coordinates of the agent
            target (list optional): destination coordinates of the agent
            debug_level: level of debug (None or 'always')

        Returns:
            object: the created agent
        """
        jid = name + "@127.0.0.1"
        agent = cls(jid, password, debug=debug_level)
        agent.set_id(name)
        agent.set_position(position)
        if target:
            agent.set_target_position(target)
        return agent

    @classmethod
    def create_agents_batch(cls, type_, number, coordinator):
        """
        Creates a batch of agents.

        Args:
            cls (class): class of the agents
            type_ (str): whether the agent is a "taxi" or a "passenger"
            number (int): size of the batch
            coordinator (:obj:`CoordinatorAgent' ): the coordinator agent
        """
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
