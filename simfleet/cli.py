# -*- coding: utf-8 -*-

"""Console script for SimFleet."""
import logging
import sys
import spade
import asyncio

import signal

import click
from loguru import logger

from simfleet.config.settings import SimfleetConfig
from simfleet.simulator import SimulatorAgent

@click.command()
@click.option("-n", "--name", help="Name of the simulation execution.")
@click.option("-o", "--output", help="Filename for saving simulation events in JSON format.")
@click.option(
    "-mt", "--max-time", help="Maximum simulation time (in seconds).", type=int
)
@click.option(
    "-r",
    "--autorun",
    help="Run simulation as soon as the agents are ready.",
    is_flag=True,
)
@click.option("-c", "--config", help="Filename of JSON file with initial config.")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Show verbose debug level: -v level 1, -vv level 2, -vvv level 3, -vvvv level 4",
)

def main(name, output, max_time, autorun, config, verbose):
    """
    Console script for SimFleet.
    """
    if verbose > 0:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

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

    simfleet_config = SimfleetConfig(config, name, max_time, verbose)

    simulator_name = "simulator_{}@{}".format(simfleet_config.simulation_name, simfleet_config.host)

    simulator = SimulatorAgent(config=simfleet_config, agentjid=simulator_name)

    # Version 3 - No funciona Crt+C ------------ Versión Javi
    # async def run_simulation():
    #
    #     #simulator = SimulatorAgent(config=simfleet_config, agentjid=simulator_name)
    #     await simulator.start()
    #
    #     if autorun:
    #         #await simulator.auto_run()
    #         await simulator.run()
    #     #else:
    #     #    await simulator.start()
    #
    #     while not simulator.is_simulation_finished():
    #         logger.warning("Simulation continue.....")
    #         try:
    #             await asyncio.sleep(0.5)
    #         except KeyboardInterrupt:
    #             logger.warning("Simulation interrupted by user.")
    #             break
    #
    #     await simulator.stop()
    #     if output:
    #         #await simulator.auto_stop(output)
    #         await simulator.write_file(output)
    #     #else:
    #     #    await simulator.stop()
    #     sys.exit(0)
    #
    # spade.run(run_simulation())


    # Versión 5 --- Añadido un evento - FUNCIONAAAAA!!!!
    async def run_simulation():
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()
        loop.add_signal_handler(signal.SIGINT, stop_event.set)

        try:
            await simulator.start()

            if autorun:
                simulator.run()

            while not simulator.is_simulation_finished() and not stop_event.is_set():
                await asyncio.sleep(0.5)

            await simulator.stop()

            if output:
                await simulator.write_file(output)

            sys.exit(0)

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            sys.exit(0)

    spade.run(run_simulation())


if __name__ == "__main__":
    main()
