from copy import copy
from typing import Optional, Generator, List, Dict

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from netqasm.sdk.classical_communication.socket import Socket
from netqasm.sdk.epr_socket import EPRSocket

from squidasm.util.routines import create_ghz

import netsquid as ns

class GraphStateDistribution(Program):
    def __init__(self, node_name: str, node_names: list):
        """
        Initializes the EntanglementSwapping.

        :param node_name: Name of the current node.
        :param node_names: List of all node names in the network, in sequence.
        """
        self.node_name = node_name

        # Find what nodes are next and prev based on the node_names list
        self.node_index = node_names.index(node_name)
        self.next_node_name = node_names[self.node_index+1] if self.node_index + 1 < len(node_names) else None
        self.prev_node_name = node_names[self.node_index-1] if self.node_index - 1 >= 0 else None

        # The remote nodes are all the nodes, but without current node. Copy the list to make the pop operation local
        self.remote_node_names = copy(node_names)
        self.remote_node_names.pop(self.node_index)

        # next and prev sockets, will be fetched from the ProgramContext using setup_next_and_prev_sockets
        self.next_socket: Optional[Socket] = None
        self.next_epr_socket: Optional[EPRSocket] = None
        self.prev_socket: Optional[Socket] = None
        self.prev_epr_socket: Optional[EPRSocket] = None

    @property
    def meta(self) -> ProgramMeta:
        # Filter next and prev node name for None values
        epr_node_names = [node for node in [self.next_node_name, self.prev_node_name] if node is not None]

        return ProgramMeta(
            name="graph_state_generation",
            csockets=self.remote_node_names,
            epr_sockets=epr_node_names,
            max_qubits=2,
        )

    def run(self, context: ProgramContext):

        print(f"{self.node_name} has index {self.node_index}")
        
        yield from self.EntanglementSwapping(context)
        
        """
        self.setup_next_and_prev_sockets(context)
        
        print(f"{self}")
        
        if self.node_index == 0:

            self.epr_qubit_0 = self.next_epr_socket.create_keep()[0]
        
        if self.node_index == 1:
                        
            self.epr_qubit_0 = self.prev_epr_socket.recv_keep()[0]
            self.epr_qubit_1 = self.next_epr_socket.create_keep()[0]

            # Perform entanglement swap
            
            self.epr_qubit_0.cnot(self.epr_qubit_1)
            self.epr_qubit_0.H()
            r0 = self.epr_qubit_0.measure()
            r1 = self.epr_qubit_1.measure()
            print(f"{self.node_name} performs Bell measurement")
            
            yield from context.connection.flush()
            
            message = f"{r0}{r1}"

            print(f"{self.node_name} measures local qubits: {r0}, {r1} and sends results to {self.next_node_name}")

            self.next_socket.send(message)
            
            yield from context.connection.flush()
            
        if self.next_epr_socket and self.node_index != 0 and self.node_index != 1 and self.node_index != 5:

            self.epr_qubit_0 = self.prev_epr_socket.recv_keep()[0]
              
            message = yield from self.prev_socket.recv()
            yield from context.connection.flush()
            print(f"{self.node_name} receives measurements {message} from {self.prev_node_name}")

            self.epr_qubit_1 = self.next_epr_socket.create_keep()[0]
                        
            # Perform entanglement swap
            
            self.epr_qubit_0.cnot(self.epr_qubit_1)
            self.epr_qubit_0.H()
            r0 = self.epr_qubit_0.measure()
            r1 = self.epr_qubit_1.measure()
            
            print(f"{self.node_name} performs Bell measurement")
                    
            yield from context.connection.flush()
            
            message = f"{r0}{r1}"            
            self.next_socket.send(message)
            
            print(f"{self.node_name} measures local qubits: {r0}, {r1} and sends results to {self.next_node_name}")
            
            yield from context.connection.flush()
        
        if self.node_index == 5:
            self.epr_qubit_0 = self.prev_epr_socket.recv_keep()[0]
            
            message = yield from self.prev_socket.recv()
            yield from context.connection.flush()
            print(f"{self.node_name} receives measurements {message} from {self.prev_node_name}")"""
                
        return {} #{"name": self.node_name, "run_time": run_time} #run_time = ns.sim_time()

    def EntanglementSwapping1(self, context: ProgramContext):
        
        self.setup_next_and_prev_sockets(context)
        # Initialize next and prev sockets using the provided context
        if self.next_epr_socket:
            self.epr_qubit_1 = self.next_epr_socket.create_keep()[0]
            
        if self.prev_epr_socket:
            self.epr_qubit_0 = self.prev_epr_socket.recv_keep()[0]

        if self.node_index in [2,4]:
            self.epr_qubit_0.cnot(self.epr_qubit_1)
            self.epr_qubit_0.H()
            r0 = self.epr_qubit_0.measure()
            r1 = self.epr_qubit_1.measure()
            print(f"{self.node_name} performs instruction[0]")
            yield from context.connection.flush()
            message = f"{r0}{r1}"
            self.next_socket.send(message)
            print(f"{self.node_name} measures local qubits: {r0}, {r1} and sends results to {self.next_node_name}")
            yield from context.connection.flush()
            
        else:
            yield from context.connection.flush()
            
            if self.node_index == 2:
                message = yield from self.prev_socket.recv()
                print(f"{self.node_name} receives measurements {message}")
                self.epr_qubit_0.cnot(self.epr_qubit_1)
                self.epr_qubit_0.H()
                r0 = self.epr_qubit_0.measure()
                r1 = self.epr_qubit_1.measure()
                print(f"{self.node_name} performs instruction[1]")
                yield from context.connection.flush()
                print(f"{self.node_name} measures local qubits: {r0}, {r1} and sends full correction to {self.next_node_name}")
                message = f"{message}{r0}{r1}"
                self.next_socket.send(message)
            else:
                yield from context.connection.flush()
                if self.node_index == 3:
                    message = yield from self.prev_socket.recv()
                    print(f"{self.node_name} recieves corrections {message}")
            
        return 0
    
    def EntanglementSwapping(self, context: ProgramContext):
        
        self.setup_next_and_prev_sockets(context)
        
        # Initialize next and prev sockets using the provided context
        if self.next_epr_socket:
            self.epr_qubit_1 = self.next_epr_socket.create_keep()[0]
            
        if self.prev_epr_socket:
            self.epr_qubit_0 = self.prev_epr_socket.recv_keep()[0]
        if self.node_index == 0:
            print(f"NAME: {self.node_name}")
            yield from context.connection.flush()
        if self.node_index == 1:
            
            self.epr_qubit_0.cnot(self.epr_qubit_1)
            self.epr_qubit_0.H()
            r0 = self.epr_qubit_0.measure()
            r1 = self.epr_qubit_1.measure()
            
            print(f"{self.node_name} performs entanglement swap")
            
            yield from context.connection.flush()
            
            message = f"{r0}{r1}"
            self.next_socket.send(message)
            print(f"{self.node_name} measures local qubits: {r0}, {r1} and sends results to {self.next_node_name}")
            
            yield from context.connection.flush()
            
        else:
            
            yield from context.connection.flush()
            
            if self.next_epr_socket and self.prev_epr_socket:
                print(f"{self.node_name}")
                message = yield from self.prev_socket.recv()
                
                print(f"{self.node_name} receives measurements {message}")
                
                self.epr_qubit_0.cnot(self.epr_qubit_1)
                self.epr_qubit_0.H()
                r0 = self.epr_qubit_0.measure()
                r1 = self.epr_qubit_1.measure()
                print(f"{self.node_name} performs entanglement swap")
                yield from context.connection.flush()
                print(f"{self.node_name} measures local qubits: {r0}, {r1} and sends correction to {self.next_node_name}")
                message = f"{message}{r0}{r1}"
                self.next_socket.send(message)
                
            elif self.prev_epr_socket:
                print(f"NAME: {self.node_name}")
                yield from context.connection.flush()

                message = yield from self.prev_socket.recv()
                
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