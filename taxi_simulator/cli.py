# -*- coding: utf-8 -*-

"""Console script for taxi_simulator."""
import click
import logging
import sys
import time

from .simulator import Simulator, SimulationConfig

logger = logging.getLogger()


@click.command()
@click.option('-n', '--name', help="Name of the simulation execution.")
@click.option('-o', '--output', help="Filename to save simulation results.")
@click.option('-of', '--oformat', help="Output format used to save simulation results. (default: json)",
              type=click.Choice(['json', 'excel']), default="json")
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
@click.option('--coord-passwd', default="coordinator_passwd",
              help="Coordinator agent password (default: coordinator_passwd).")
@click.option('-rn', '--route-name', default="route",
              help="Route agent name (default: route).")
@click.option('--route-passwd', default="route_passwd",
              help="Route agent password (default: route_passwd).")
@click.option('--host', help="XMPP server address")
@click.option('-ip', '--ip-address', default="127.0.0.1", help="IP to serve web (default: 127.0.0.1).")
@click.option('-v', '--verbose', count=True,
              help="Show verbose debug level: -v level 1, -vv level 2, -vvv level 3, -vvvv level 4")
def main(name, output, oformat, max_time, autorun, taxi, passenger, coordinator, port, num_taxis, num_passengers,
         scenario, coordinator_name, coord_passwd, route_name, route_passwd, host, ip_address, verbose):
    """
    Console script for taxi_simulator.
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
    config.coordinator_password = coord_passwd
    config.route_name = route_name
    config.route_password = route_passwd
    config.host = host
    config.ip = ip_address
    config.verbose = verbose

    simulator = Simulator(config)

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
