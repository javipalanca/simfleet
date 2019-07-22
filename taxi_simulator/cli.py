# -*- coding: utf-8 -*-

"""Console script for SimFleet."""
import click
import logging
import sys
import time

from .simulator import SimulatorAgent, SimulationConfig

logger = logging.getLogger()


@click.command()
@click.option('-n', '--name', help="Name of the simulation execution.")
@click.option('-o', '--output', help="Filename to save simulation results.")
@click.option('-of', '--oformat', help="Output format used to save simulation results. (default: json)",
              type=click.Choice(['json', 'excel']), default="json")
@click.option('-mt', '--max-time', help="Maximum simulation time (in seconds).", type=int)
@click.option('-r', '--autorun', help="Run simulation as soon as the agents are ready.", is_flag=True)
@click.option('-t', '--transport', default="taxi_simulator.strategies.AcceptAlwaysStrategyBehaviour",
              help='Taxi strategy class (default: AcceptAlwaysStrategyBehaviour).')
@click.option('-c', '--customer', default="taxi_simulator.strategies.AcceptFirstRequestTaxiBehaviour",
              help="Passenger strategy class (default: AcceptFirstRequestTaxiBehaviour).")
@click.option('-c', '--fleetmanager', default="taxi_simulator.strategies.DelegateRequestTaxiBehaviour",
              help="fleetmanager strategy class (default: DelegateRequestTaxiBehaviour).")
@click.option('--port', default=9000, help="Web interface port (default: 9000).")
@click.option('-nt', '--num-transports', default=0, help="Number of initial transports to create (default: 0).")
@click.option('-np', '--num-customers', default=0, help="Number of initial customers to create (default: 0).")
@click.option('-nm', '--num-managers', default=3, help="Number of initial managers to create (default: 3)")
@click.option('--scenario', help="Filename of JSON file with initial scenario description.")
@click.option('-cn', '--fleetmanager-name', default="fleetmanager",
              help="fleetmanager agent name (default: fleetmanager).")
@click.option('--coord-passwd', default="fleetmanager_passwd",
              help="fleetmanager agent password (default: fleetmanager_passwd).")
@click.option('-rn', '--route-name', default="route",
              help="Route agent name (default: route).")
@click.option('--route-passwd', default="route_passwd",
              help="Route agent password (default: route_passwd).")
@click.option('--host', help="XMPP server address")
@click.option('-ip', '--ip-address', default="127.0.0.1", help="IP to serve web (default: 127.0.0.1).")
@click.option('-v', '--verbose', count=True,
              help="Show verbose debug level: -v level 1, -vv level 2, -vvv level 3, -vvvv level 4")
def main(name, output, oformat, max_time, autorun, transport, customer, fleetmanager, port, num_transports, num_customers,
         num_managers, scenario, fleetmanager_name, coord_passwd, route_name, route_passwd, host, ip_address, verbose):
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

    config = SimulationConfig()
    config.simulation_name = name
    config.max_time = max_time
    config.transport_strategy = transport
    config.customer_strategy = customer
    config.fleetmanager_strategy = fleetmanager
    config.scenario = scenario
    config.num_transport = num_transports
    config.num_customers = num_customers
    config.num_managers = num_managers
    config.http_port = port
    config.fleetmanager_name = fleetmanager_name
    config.fleetmanager_password = coord_passwd
    config.route_name = route_name
    config.route_password = route_passwd
    config.host = host
    config.ip = ip_address
    config.verbose = verbose

    simulator = SimulatorAgent(config)

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
