# -*- coding: utf-8 -*-

"""Console script for SimFleet."""
import click
import logging
import sys
import time

from .config import SimfleetConfig
from .simulator import SimulatorAgent

logger = logging.getLogger()


@click.command()
@click.option('-n', '--name', help="Name of the simulation execution.")
@click.option('-o', '--output', help="Filename to save simulation results.")
@click.option('-of', '--oformat', help="Output format used to save simulation results. (default: json)",
              type=click.Choice(['json', 'excel']), default="json")
@click.option('-mt', '--max-time', help="Maximum simulation time (in seconds).", type=int)
@click.option('-r', '--autorun', help="Run simulation as soon as the agents are ready.", is_flag=True)
@click.option('-c', '--config', help="Filename of JSON file with initial config.")
@click.option('-v', '--verbose', count=True,
              help="Show verbose debug level: -v level 1, -vv level 2, -vvv level 3, -vvvv level 4")
def main(name, output, oformat, max_time, autorun, scenario, config, verbose):
    """
    Console script for SimFleet.
    """
    if verbose > 0:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aioopenssl").setLevel(logging.WARNING)
    logging.getLogger("aiosasl").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("spade").setLevel(logging.WARNING)
    if verbose > 2:
        logging.getLogger("spade").setLevel(logging.INFO)
    if verbose > 3:
        logging.getLogger("aioxmpp").setLevel(logging.INFO)
    else:
        logging.getLogger("aioxmpp").setLevel(logging.WARNING)

    simfleet_config = SimfleetConfig(config)
    simfleet_config.simulation_name = name
    simfleet_config.max_time = max_time
    simfleet_config.verbose = verbose

    simulator_name = "simulator_{}@{}".format(name, simfleet_config.host)

    simulator = SimulatorAgent(config=simfleet_config, agentjid=simulator_name)
    simulator.start()

    if autorun:
        simulator.run()

    while not simulator.is_simulation_finished():
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            break

    simulator.stop()
    if output:
        simulator.write_file(output, oformat)

    sys.exit(0)


if __name__ == "__main__":
    main()
