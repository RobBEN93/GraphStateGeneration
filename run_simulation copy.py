from graphapplication import GraphStateDistribution

from squidasm.run.stack.config import StackNetworkConfig
from squidasm.run.stack.run import run

from squidasm.sim.stack.common import LogManager  # Import LogManager for logging

from tests.yaml_to_nx import yaml_to_nx
from collections import defaultdict

# Set up logging
LogManager.set_log_level("INFO")

# Disable logging to terminal
logger = LogManager.get_stack_logger()
logger.handlers = []
# Enable logging to file
LogManager.log_to_file("logs/info.log")

# import network configuration from file
cfg = StackNetworkConfig.from_file("smallworldtennodeconfig.yaml")
#G = yaml_to_nx("network_config_noisy.yaml"

# Extract the list of node names
nodes = [stack.name for stack in cfg.stacks]

# Dictionary to hold the peers for each node
peers = defaultdict(set)
for link in cfg.links:
    peers[link.stack1].add(link.stack2)
    peers[link.stack2].add(link.stack1)
for node in peers:
    peers[node] = sorted(peers[node], key=lambda x: int(x.split('_')[1]))
    
programs = {
    node: GraphStateDistribution(node_name=node, peer_names=peers[node])
    for node in nodes
}

run(config=cfg, programs=programs, num_times=1)