from copy import copy
from typing import Optional, Generator, List, Dict

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from netqasm.sdk.classical_communication.socket import Socket
from netqasm.sdk.epr_socket import EPRSocket

from squidasm.sim.stack.common import LogManager

from squidasm.util.routines import create_ghz

import netsquid as ns

class GraphStateDistribution(Program):
    
    def __init__(self, node_name: str, connected_node_names: list, peer_names: list):
        """
        :param node_name: Name of the current node.
        :param connected_node_names: List of all node names in the network, in sequence.
        """
        
        self.node_name = node_name
        
        self.peer_names = peer_names

        # Find what nodes are next and prev based on the connected_node_names list
        self.node_index = connected_node_names.index(node_name)
        self.next_node_name = connected_node_names[self.node_index+1] if self.node_index + 1 < len(connected_node_names) else None
        self.prev_node_name = connected_node_names[self.node_index-1] if self.node_index - 1 >= 0 else None

        # The remote nodes are all the nodes, but without current node. Copy the list to make the pop operation local
        self.remote_node_names = copy(connected_node_names)
        self.remote_node_names.pop(self.node_index)

        # next and prev sockets, will be fetched from the ProgramContext using setup_next_and_prev_sockets
        self.next_socket: Optional[Socket] = None
        self.next_epr_socket: Optional[EPRSocket] = None
        self.prev_socket: Optional[Socket] = None
        self.prev_epr_socket: Optional[EPRSocket] = None
        
        for peer in peer_names:
            setattr(self,f"csocket_{peer}", None)
            setattr(self,f"epr_socket_{peer}", None)
            
        self.logger = LogManager.get_stack_logger(f"{self.node_name} program")

    @property
    def meta(self) -> ProgramMeta:

        return ProgramMeta(
            name="graph_state_generation",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=len(self.peer_names),
        )

    def run(self, context: ProgramContext):
        
        logger = self.logger
        logger.info(f"{self.node_name} has index {self.node_index}")


        self.setup_sockets(context)
        
        yield from self.EntanglementSwapping(context)

        return {} #{"name": self.node_name, "run_time": run_time} #run_time = ns.sim_time()
    
    def setup_sockets(self, context: ProgramContext):
        for peer in self.peer_names:
            setattr(self,f"csocket_{peer}", context.csockets[self.peer])
            setattr(self,f"epr_socket_{peer}", context.epr_sockets[self.peer])
    
    def EntanglementSwapping(self, context: ProgramContext, end_nodes: tuple):
        
        self.setup_next_and_prev_sockets(context)
        
        print(f"Current node: {self.node_name}")
        
        # Initialize next and prev sockets using the provided context
        if self.next_epr_socket:
            self.epr_qubit_1 = self.next_epr_socket.create_keep()[0]
            print(f"{self.node_name} creates EPR pair and sends it to {self.next_node_name}")
            
        if self.prev_epr_socket:
            self.epr_qubit_0 = self.prev_epr_socket.recv_keep()[0]
            print(f"{self.node_name} recieves EPR pair from {self.prev_node_name}")
            
        if self.node_index == 1:
            print(f"Current node: {self.node_name}")
            # Perform entanglement swap
            self.epr_qubit_0.cnot(self.epr_qubit_1)
            self.epr_qubit_0.H()
            r0 = self.epr_qubit_0.measure()
            r1 = self.epr_qubit_1.measure()
            
            self.logger.info(f"{self.node_name} performs entanglement swap")
            print(f"{self.node_name} performs entanglement swap")
            
            yield from context.connection.flush()
            
            message = f"{r0}{r1}"
            self.next_socket.send(message)
            self.logger.info(f"{self.node_name} measures local qubits: {r0}, {r1} and sends results to {self.next_node_name}")
            print(f"{self.node_name} measures local qubits: {r0}, {r1} and sends results to {self.next_node_name}")
            
            yield from context.connection.flush()
            
        else:
            
            yield from context.connection.flush()
            
            if self.next_epr_socket and self.prev_epr_socket:
                
                print(f"Current node: {self.node_name}")
                # Receive measurement results from previous node
                message = yield from self.prev_socket.recv()
                
                self.logger.info(f"{self.node_name} receives measurements {message}")
                print(f"{self.node_name} receives measurements {message}")
                
                # Perform entanglement swap
                
                self.epr_qubit_0.cnot(self.epr_qubit_1)
                self.epr_qubit_0.H()
                r0 = self.epr_qubit_0.measure()
                r1 = self.epr_qubit_1.measure()
                
                self.logger.info(f"{self.node_name} performs entanglement swap")
                print(f"{self.node_name} performs entanglement swap")
                
                yield from context.connection.flush()
                
                self.logger.info(f"{self.node_name} measures local qubits: {r0}, {r1} and sends correction to {self.next_node_name}")
                print(f"{self.node_name} measures local qubits: {r0}, {r1} and sends correction to {self.next_node_name}")
                
                message = f"{message}{r0}{r1}"
                self.next_socket.send(message)
                
            elif self.prev_epr_socket:
                
                print(f"Current node: {self.node_name}")
                
                message = yield from self.prev_socket.recv()
                
                self.logger.info(f"{self.node_name} recieves corrections {message}")
                print(f"{self.node_name} recieves corrections {message}")
            
        return 0

    def setup_next_and_prev_sockets(self, context: ProgramContext):
        """Initializes next and prev sockets using the given context."""
        if self.next_node_name:
            self.next_socket = context.csockets[self.next_node_name]
            self.next_epr_socket = context.epr_sockets[self.next_node_name]
                        
        if self.prev_node_name:
            self.prev_socket = context.csockets[self.prev_node_name]
            self.prev_epr_socket = context.epr_sockets[self.prev_node_name]
    
    def gen_ghz(self, context: ProgramContext):
        """Generates GHZ state on the whole network."""
        qubit, m = yield from create_ghz(
            context.connection,
            self.prev_epr_socket,
            self.next_epr_socket,
            self.prev_socket,
            self.next_socket,
            do_corrections=True,
        )

        yield from context.connection.flush()
        
        return qubit
    """
    
    # Perform local corrections based on the result
    if result == "00":
        logger.info(f"Result is 00, no correction needed for {self.name}.")
        print((f"Result is 00, no correction needed for {self.name}."))
    elif result == "01":
        logger.info(f"Result is 01, applying Pauli-X correction for {self.name}.")
        print(f"Result is 01, applying Pauli-X correction for {self.name}.")
        epr_qubit_down.X()  # Apply Pauli-X correction
    elif result == "10":
        logger.info(f"Result is 10, applying Pauli-Z correction for {self.name}.")
        print(f"Result is 10, applying Pauli-Z correction for {self.name}.")
        epr_qubit_down.Z()  # Apply Pauli-Z correction
    elif result == "11":
        logger.info(f"Result is 11, applying Pauli-X and Pauli-Z correction for {self.name}.")
        print(f"Result is 11, applying Pauli-X and Pauli-Z correction for {self.name}.")
        epr_qubit_down.X()  # Apply Pauli-X
        epr_qubit_down.Z()  # Apply Pauli-Z
    """