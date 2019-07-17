import json
import logging
logger = logging.getLogger()


class Scenario(object):
    """
    A scenario object reads a file with a JSON representation of a scenario and is used to create the participant agents.
    """

    def __init__(self, filename):
        """
        The Scenario constructor reads the JSON file and creates the defined agents found in that file.
        Args:
            filename (str): the name of the scenario file
        """
        self.scenario = None
        with open(filename, 'r') as f:
            logger.info("Reading scenario {}".format(filename))
            self.scenario = json.load(f)
