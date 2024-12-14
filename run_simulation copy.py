from application import GraphStateDistribution

from squidasm.run.stack.config import StackNetworkConfig
from squidasm.run.stack.run import run

from squidasm.sim.stack.common import LogManager  # Import LogManager for logging

from tests.yaml_to_nx import yaml_to_nx

# Set up logging
LogManager.set_log_level("INFO")

# Disable logging to terminal
logger = LogManager.get_stack_logger()
logger.handlers = []
# Enable logging to file
LogManager.log_to_file("/home/vor/VSCodeProjects/QIA-Challenge/logs/info.log")

# import network configuration from file
cfg = StackNetworkConfig.from_file("network_config_ideal.yaml")
G = yaml_to_nx("network_config_noisy.yaml")
print(cfg)

# Extract the list of node names
nodes = [stack.name for stack in cfg.stacks]

def optimized_resource_state(requests):
    # Calculate adjacency matrices
    return 0
    

#request = optimized_resource_state()