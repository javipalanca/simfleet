# -*- coding: utf-8 -*-

"""Console script for taxi_simulator."""
import click
import logging
import sys
import time

from simulator import Simulator, SimulationConfig

logger = logging.getLogger()


@click.command()
@click.option('-n', '--name', help="Name of the simulation execution.")
@click.option('-o', '--output', help="Filename to save simulation results.")
@click.option('-mt', '--max-time', help="Maximum simulation time (in seconds).", type=int)
@click.option('-r', '--autorun', help="Run simulation as soon as the agents are ready.", is_flag=True)
@click.option('-t', '--taxi', default="taxi_simulator.strategies.AcceptAlwaysStrategyBehaviour",
              help='Taxi strategy class (default: AcceptAlwaysStrategyBehaviour).')
@click.option('-p', '--passenger', default="taxi_simulator.strategies.AcceptFirstRequestTaxiBehaviour",
              help="Passenger strategy class (default: AcceptFirstRequestTaxiBehaviour).")
@click.option('-c', '--coordinator', default="taxi_simulator.strategies.DelegateRequestTaxiBehaviour",
              help="Coordinator strategy class (default: DelegateRequestTaxiBehaviour).")
@click.option('--port', default=9000, help="Web interface port (default: 9000).")
@click.option('-nt', '--num-taxis', default=0, help="Number of initial taxis to create (default: 0).")
@click.option('-np', '--num-passengers', default=0, help="Number of initial passengers to create (default: 0).")
@click.option('--scenario', help="Filename of JSON file with initial scenario description.")
@click.option('-cn', '--coordinator-name', default="coordinator",
              help="Coordinator agent name (default: coordinator).")
@click.option('--passwd', default="coordinator_passwd",
              help="Coordinator agent password (default: coordinator_passwd).")
@click.option('-bp', '--backend-port', default=5000, help="Backend port (default: 5000).")
@click.option('-v', '--verbose', count=True,
              help="Show verbose debug level: -v level 1, -vv level 2, -vvv level 3, -vvvv level 4")
def main(name, output, max_time, autorun, taxi, passenger, coordinator, port, num_taxis, num_passengers, scenario,
         coordinator_name, passwd, backend_port, verbose):
    """Console script for taxi_simulator."""
    if verbose > 0:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = SimulationConfig()
    config.simulation_name = name
    config.max_time = max_time
    config.taxi_strategy = taxi
    config.passenger_strategy = passenger
    config.coordinator_strategy = coordinator
    config.scenario = scenario
    config.num_taxis = num_taxis
    config.num_passengers = num_passengers
    config.http_port = port
    config.coordinator_name = coordinator_name
    config.coordinator_password = passwd
    config.backend_port = backend_port
    config.verbose = verbose

    simulator = Simulator(config)

    if autorun:
        simulator.run()

    while not simulator.is_simulation_finished():
        try:
            time.sleep(0.5)
            simulator.process_queue()
        except KeyboardInterrupt:
            break

    simulator.stop()

    sys.exit(0)


if __name__ == "__main__":
    main()
