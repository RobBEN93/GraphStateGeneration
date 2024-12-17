from copy import copy
from typing import Optional, Generator, List, Dict, Tuple

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from netqasm.sdk.classical_communication.socket import Socket
from netqasm.sdk.epr_socket import EPRSocket

from squidasm.sim.stack.common import LogManager

from squidasm.util.routines import create_ghz

import netsquid as ns

request = [('node_0','node_1'),('node_0','node_6'),('node_1','node_2'),('node_1','node_6')]

example_path = ['node_0','node_1','node_2','node_3','node_4','node_8']

example_path2 = ['node_0','node_1','node_2']

class GraphStateDistribution(Program):
    
    def __init__(self, node_name: str, peer_names: list):
        """
        :param node_name: Name of the current node.
        :param connected_node_names: List of all node names in the network, in path.
        """
        
        self.node_name = node_name
        self.peer_names = peer_names
        
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
            max_qubits=2,
        )

    def run(self, context: ProgramContext):
        
        logger = self.logger
        logger.info(f"{self.node_name}")

        self.setup_sockets(context)
        
        #print(f"{self.node_name} has peers {self.peer_names}")
        
        #yield from self.send_msg_to_peers(context)
        #yield from self.recv_msg_from_peers(context)
        #yield from self.send_msg_to_dist_node(context,path=example_path,message="Hi!!!")
        #yield from self.dist_node_epr_pair(context,example_path,False)
        #yield from self.dist_node_epr_pair(context,example_path2,True)
        #yield from self.create_bell_pair(context,"node_0","node_1")
        yield from self.generate_graph_state(context,request)
        #path = ["node_1","node_0","node_6"]
        #yield from self.dist_node_epr_pair(context,path,True)
        """
        if self.node_name == "node_1":
            r1=self.epr_qubit_1.measure()
            yield from context.connection.flush()
            print(f"LEFT RESULT --------------------------------- {r1}")
            
        elif self.node_name == "node_6":
            r0=self.epr_qubit_0.measure()
            yield from context.connection.flush()
            print(f"RIGHT RESULT --------------------------------- {r0}")
            print(f" ")
        
        
        else:
            yield from context.connection.flush()
        
        
        
        
        if self.node_name == request[0][0] and self.peer_names[0] == request[0][1]:
            peer_epr_socket = getattr(self, f"epr_socket_{self.peer_names[0]}")
            self.epr_qubit_0 = peer_epr_socket.create_keep()[0]
            print(f"{self.node_name} creates EPR pair and sends it to {self.peer_names[0]}")
            
        elif self.node_name == request[0][1]:
            print("HI!!!!!!")
        """
        
        # yield from self.entanglement_swapping(context)

        return {} #{"name": self.node_name, "run_time": run_time} #run_time = ns.sim_time()
    
    def generate_graph_state(self, context: ProgramContext, request = request):
        # Check if current node appears in the request and if so how many times
        count = GraphStateDistribution.count_node_occurrences(request=request,node_name=self.node_name)
        for edge in request:
            try:
                yield from self.create_bell_pair(context,edge[0],edge[1])
            except:
                print("Not a peer")
            try:
                path = ["node_1","node_3","node_5","node_7","node_6"]
                yield from self.dist_node_epr_pair(context,path,True)
            except:
                print("not a peer")
       
       
    def gen_graph_state(self, context: ProgramContext, request = [('node_0','node_1'),('node_1','node_2')]):
        
        if self.node_name in request[0]:
            #self.current_index = request.index(self.node_name)
            if self.node_name == request[0][0]:
                epr_socket = getattr(self, f"epr_socket_{request[0][1]}")
                self.epr_qubit_0 = epr_socket.create_keep()[0]
                print(f"{self.node_name} sends epr pair to {request[0][1]}")
                
                self.epr_qubit_0.H()
                r0 = self.epr_qubit_0.measure()
                
                yield from context.connection.flush()
                
                print(r0)
                
            elif self.node_name == request[0][1]:
                epr_socket = getattr(self, f"epr_socket_{request[0][0]}")
                self.epr_qubit_0 = epr_socket.recv_keep()[0]
                print(f"{self.node_name} receives epr pair from {request[0][0]}")
                r0 = self.epr_qubit_0.measure()
                yield from context.connection.flush()
                print(r0)
                
            else:           
                yield from context.connection.flush()

        else:
            yield from context.connection.flush()
            
        return 0
    
    def recv_msg_from_peers(self, context: ProgramContext):
        message = []
        for peer in self.peer_names:
            socket = getattr(self, f"csocket_{peer}", None)
            if socket is not None:
                msg = yield from socket.recv()
                print(f"{self.node_name} receives <{msg}> from {peer}")
                message.append(msg)
            else:
                message.append(None)
        return message
    
    def send_msg_to_peers(self, context: ProgramContext, message: Optional[str] = None):
        if message is None:
            message = f"HI from {self.node_name}"
        for peer in self.peer_names:
            socket = getattr(self, f"csocket_{peer}", None)
            socket.send(message)
            print(f"{self.node_name} sends <{message}> to {peer}")
            yield from context.connection.flush()
        return 0
    
    def send_msg_to_dist_node(self, context: ProgramContext, path: List,  message: Optional[str] = None):
        
        if self.node_name in path:
            self.current_index = path.index(self.node_name)
            if self.node_name == path[0]:
                csocket = getattr(self, f"csocket_{path[1]}")
                #print(f"{self.node_name} sends <{message}> to {path[1]}")
                csocket.send(message)
            elif self.node_name != path[-1]:
                csocket_prev = getattr(self, f"csocket_{path[self.current_index-1]}")
                msg = yield from csocket_prev.recv()
                #print(f"{self.node_name} receives <{msg}> from {path[self.current_index-1]}")

                csocket_next = getattr(self, f"csocket_{path[self.current_index+1]}")
                #print(f"{self.node_name} sends <{msg}> to {path[self.current_index+1]}")

                csocket_next.send(msg)
            else:
                csocket_prev = getattr(self, f"csocket_{path[self.current_index-1]}")
                msg = yield from csocket_prev.recv()
                #print(f"{self.node_name} receives <{msg}> from {path[self.current_index-1]}")
                
                return msg
        else:
            yield from context.connection.flush()
            
        return 0
    
    def setup_sockets(self, context: ProgramContext):
        for peer in self.peer_names:
            setattr(self,f"csocket_{peer}", context.csockets[peer])
            setattr(self,f"epr_socket_{peer}", context.epr_sockets[peer])
    
    def create_bell_pair(self, context: ProgramContext, node1: str, node2: str):
        """
        This function establishes a Bell pair between two adjacent nodes, node1 and node2.
        """
        # Check if this node is one of the specified nodes
        if self.node_name in [node1, node2]:

            if self.node_name == node1:
                epr_socket_next = getattr(self, f"epr_socket_{node2}")
                self.epr_qubit_1 = epr_socket_next.create_keep()[0]
                self.logger.info(f"{self.node_name} creates EPR pair and sends it to {node2}")
                print(f"{self.node_name} creates EPR pair and sends it to {node2}")
                
                return self.epr_qubit_1
                
            elif self.node_name == node2:
                epr_socket_prev = getattr(self, f"epr_socket_{node1}")
                self.epr_qubit_0 = epr_socket_prev.recv_keep()[0]
                self.logger.info(f"{self.node_name} receives EPR pair from {node1}")
                print(f"{self.node_name} receives EPR pair from {node1}")

                return self.epr_qubit_0

        else:
            yield from context.connection.flush()
            #print(f"{self.node_name} is not involved in the Bell pair creation between {node1} and {node2}")
    
    def dist_node_epr_pair(self, context: ProgramContext, path: List, apply_correction: bool = True):
        """
        This function generates an EPR pair between two nodes Bell states are tracked on each node
        so that only the end node applies a correction to get a |phi+> state

        We know an initial |phi+>\otimes|phi+>\otimes ... \otimes|phi+> state is initially established
        so based on the result of the Bell measurement we know the next node starts in one of eight
        possible cases, (which we identify with the following strings):
                case     :  id   
            |phi+>|phi+> :  00
            |psi+>|phi+> :  01
            |phi->|phi+> :  10
            |psi->|phi+> :  11
           -|phi+>|phi+> : -00
           -|psi+>|phi+> : -01
           -|phi->|phi+> : -10
           -|psi->|phi+> : -11
           
        So each node that performs entanglement swapping only sends information about what state is present
        to the next node and not the measurement result itself, and only the end nodes perform a correction
        Notice that from the final Bell measurement the given case by the check_case function is the actual  
        state +-|phi+-> or +-|psi+->, to which we correct accordingly with the apply_correction method
        
        Additionally, some of the corrections require gate operations on both end nodes so when apply_correction
        is true, the final state is sent back to the starting node.
        """

        # Establish EPR pairs along connected nodes on the path
        
        if self.node_name in path:
            self.current_index = path.index(self.node_name)
            if self.node_name == path[0]:
                epr_socket_next = getattr(self, f"epr_socket_{path[1]}")
                csocket_next = getattr(self, f"csocket_{path[1]}")
                self.epr_qubit_1 = epr_socket_next.create_keep()[0]
                self.logger.info(f"{self.node_name} creates EPR pair and sends it to {path[1]}")
                #print(f"{self.node_name} creates EPR pair and sends it to {path[1]}")
                
            elif self.node_name != path[-1]:
                epr_socket_prev = getattr(self, f"epr_socket_{path[self.current_index-1]}")
                csocket_prev = getattr(self, f"csocket_{path[self.current_index-1]}")
                self.epr_qubit_0 = epr_socket_prev.recv_keep()[0]
                self.logger.info(f"{self.node_name} receives EPR pair from {path[self.current_index-1]}")
                #print(f"{self.node_name} receives EPR pair from {path[self.current_index-1]}")
                
                epr_socket_next = getattr(self, f"epr_socket_{path[self.current_index+1]}")
                csocket_next = getattr(self, f"csocket_{path[self.current_index+1]}")
                self.epr_qubit_1 = epr_socket_next.create_keep()[0]
                self.logger.info(f"{self.node_name} creates EPR pair and sends it to {path[self.current_index+1]}")
                #print(f"{self.node_name} creates EPR pair and sends it to {path[self.current_index+1]}")

            else:
                epr_socket_prev = getattr(self, f"epr_socket_{path[self.current_index-1]}")
                csocket_prev = getattr(self, f"csocket_{path[self.current_index-1]}")
                self.epr_qubit_0 = epr_socket_prev.recv_keep()[0]
                self.logger.info(f"{self.node_name} receives EPR pair from {path[self.current_index-1]}")
                #print(f"{self.node_name} receives EPR pair from {path[self.current_index-1]}")
        else:
            yield from context.connection.flush()
        
        # Perform chain of entanglement swapping
        if self.node_name in path:
            
            if self.node_name == path[1]:
                
                # Second node in the chain performs the first Bell measurement and sends result to next node
                self.epr_qubit_0.cnot(self.epr_qubit_1)
                self.epr_qubit_0.H()
                r0 = self.epr_qubit_0.measure()
                r1 = self.epr_qubit_1.measure()
                self.logger.info(f"{self.node_name} performs entanglement swap")
                #print(f"{self.node_name} performs entanglement swap")
                
                yield from context.connection.flush()

                result = f"{r0}{r1}"
                csocket_next.send(result)
                self.logger.info(f"{self.node_name} measures local qubits: {result}. Sends case {result} to {path[self.current_index+1]}")
                #print(f"{self.node_name} measures local qubits: {result}. Sends case {result} to {path[self.current_index+1]}")

                yield from context.connection.flush()
                
                if apply_correction:
                    yield from self.send_msg_to_dist_node(context,list(reversed(path)))
                    # Confirm correction
                    yield from self.send_msg_to_dist_node(context,path)


            else:
                yield from context.connection.flush()

                if self.node_name != path[-1] and self.node_name != path[0]:
                    
                    # Wait for measurement results from previous node
                    current_case = yield from csocket_prev.recv()
                    
                    self.logger.info(f"{self.node_name} receives case {current_case}")
                    #print(f"{self.node_name} receives case {current_case}")
                    
                    # Perform entanglement swap and send case to next node
                    self.epr_qubit_0.cnot(self.epr_qubit_1)
                    self.epr_qubit_0.H()
                    r0 = self.epr_qubit_0.measure()
                    r1 = self.epr_qubit_1.measure()
                    
                    self.logger.info(f"{self.node_name} performs entanglement swap")
                    #print(f"{self.node_name} performs entanglement swap")
                    
                    yield from context.connection.flush()
                    
                    measurement = f"{r0}{r1}"
                    
                    case = GraphStateDistribution.check_case(prev_case=current_case, current_measurement=measurement)
                    
                    self.logger.info(f"{self.node_name} measures local qubits: {r0}{r1}. Sends case {case} to {path[self.current_index+1]}")
                    #print(f"{self.node_name} measures local qubits: {r0}{r1}. Sends case {case} to {path[self.current_index+1]}")

                    csocket_next.send(case)

                    if apply_correction:
                        yield from self.send_msg_to_dist_node(context,list(reversed(path)))
                        # Confirm correction
                        yield from self.send_msg_to_dist_node(context,path)

                    
                elif self.node_name == path[-1]:
                    
                    # Final node receives final measurement and applies corrections if selected
                    current_case = yield from csocket_prev.recv()
                    
                    self.logger.info(f"{self.node_name} recieves case {current_case}")
                    #print(f"{self.node_name} recieves case {current_case}")
                    if apply_correction:
                        yield from self.send_msg_to_dist_node(context,list(reversed(path)),current_case)
                        yield from self.apply_swap_correction(context,current_case,"end")
                        # Confirm correction
                        yield from self.send_msg_to_dist_node(context,path)
                    else:
                        return self.epr_qubit_0, current_case
                
                elif self.node_name == path[0]:
                    # First node does not perform any operation after generating its EPR pair with the following node
                    # except when apply_correction is selected, in which case it waits for the information on the needed
                    # Pauli operations
                    if apply_correction:
                        msg = yield from self.send_msg_to_dist_node(context,list(reversed(path)))

                        yield from self.apply_swap_correction(context,msg,"start")
                        # Confirm correction
                        yield from self.send_msg_to_dist_node(context,path,"confirmation")
                        return self.epr_qubit_1
                    
                    else:
                        return self.epr_qubit_1
        else:
            yield from context.connection.flush()
            
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
    
    def apply_swap_correction(self, context: ProgramContext, case, node):
        if node == "end":
            if case == "00":
                self.logger.info(f"State is |phi+>. No correction needed for {self.node_name}.")
                print((f"State is |phi+>. No correction needed for {self.node_name}."))
            elif case == "01":
                self.logger.info(f"State is |psi+>. Applying Pauli-X correction at {self.node_name}.")
                print(f"State is |psi+>. applying Pauli-X correction at {self.node_name}.")
                self.epr_qubit_0.X()
            elif case == "10":
                self.logger.info(f"State is |phi->. Applying Pauli-Z correction at {self.node_name}.")
                print(f"State is |phi->. Applying Pauli-Z correction at {self.node_name}.")
                self.epr_qubit_0.Z()
            elif case == "11":
                self.logger.info(f"State is |psi->. Applying Pauli-X and Pauli-Z correction at {self.node_name}.")
                print(f"State is |psi->. applying Pauli-X and Pauli-Z correction at {self.node_name}.")
                self.epr_qubit_0.X()
                self.epr_qubit_0.Z()
            elif case == "-00":
                self.logger.info(f"State is -|phi+>. Applying XZX correction at {self.node_name}.")
                print((f"State is -|phi+>. Applying XZX correction at {self.node_name}."))
                self.epr_qubit_0.X()
                self.epr_qubit_0.Z()
                self.epr_qubit_0.X()
            elif case == "-01":
                self.logger.info(f"State is -|psi+>. Applying XZ correction at {self.node_name}.")
                print(f"State is -|psi+>. Applying XZ correction at {self.node_name}.")
                self.epr_qubit_0.Z()
                self.epr_qubit_0.X()
            elif case == "-10":
                self.logger.info(f"State is -|phi->. Applying ZX correction at {self.node_name}.")
                print(f"State is -|phi->. Applying ZX correction at {self.node_name}.")
                self.epr_qubit_0.X()
                self.epr_qubit_0.Z()
            elif case == "-11":
                self.logger.info(f"State is -|psi->. Applying XZ correction at {self.node_name}.")
                print(f"State is -|psi->. Applying XZ correction at {self.node_name}.")
                self.epr_qubit_0.Z()
                self.epr_qubit_0.X()
        if node == "start":
            if case == "00":
                self.logger.info(f"State is |phi+>. No correction needed for {self.node_name}.")
                print((f"State is |phi+>. No correction needed for {self.node_name}."))
            elif case == "01":
                self.logger.info(f"State is |psi+>. No correction needed for {self.node_name}.")
                print(f"State is |psi+>. No correction needed for {self.node_name}.")
            elif case == "10":
                self.logger.info(f"State is |phi->. No correction needed for {self.node_name}.")
                print(f"State is |phi->. No correction needed for {self.node_name}.")
            elif case == "11":
                self.logger.info(f"State is |psi->. No correction needed for {self.node_name}.")
                print(f"State is |psi->. No correction needed for {self.node_name}.")
            elif case == "-00":
                self.logger.info(f"State is -|phi+>. Applying Pauli-Z correction at {self.node_name}.")
                print((f"State is -|phi+>. Applying Pauli-Z correction at {self.node_name}."))
                self.epr_qubit_1.Z()
            elif case == "-01":
                self.logger.info(f"State is -|psi+>. Applying Pauli-Z correction at {self.node_name}.")
                print(f"State is -|psi+>. Applying Pauli-Z correction at {self.node_name}.")
                self.epr_qubit_1.Z()
            elif case == "-10":
                self.logger.info(f"State is -|phi->. Applying Pauli-X correction at {self.node_name}.")
                print(f"State is -|phi->. Applying Pauli-X correction at {self.node_name}.")
                self.epr_qubit_1.X()
            elif case == "-11":
                self.logger.info(f"State is -|psi->.  No correction needed for {self.node_name}.")
                print(f"State is -|psi->. No correction needed for {self.node_name}.")
        yield from context.connection.flush()
        
    @staticmethod
    def check_case(prev_case, current_measurement):
        """ Checks what Bell states are involved in the current nodes given the previous case and current measurement results"""
        if prev_case == "00":
            if current_measurement == "00":
                new_case = "00"
            elif current_measurement == "01":
                new_case = "01"
            elif current_measurement == "10":
                new_case = "10"
            elif current_measurement == "11":
                new_case = "11"
        elif prev_case == "01":
            if current_measurement == "00":
                new_case = "01"
            elif current_measurement == "01":
                new_case = "00"
            elif current_measurement == "10":
                new_case = "-11"
            elif current_measurement == "11":
                new_case = "-10"
        elif prev_case == "10":
            if current_measurement == "00":
                new_case = "10"
            elif current_measurement == "01":
                new_case = "11"
            elif current_measurement == "10":
                new_case = "00"
            elif current_measurement == "11":
                new_case = "01"
        elif prev_case == "11":
            if current_measurement == "00":
                new_case = "11"
            elif current_measurement == "01":
                new_case = "10"
            elif current_measurement == "10":
                new_case = "-01"
            elif current_measurement == "11":
                new_case = "-00"
        elif prev_case == "-00":
            if current_measurement == "00":
                new_case = "-00"
            elif current_measurement == "01":
                new_case = "-01"
            elif current_measurement == "10":
                new_case = "-10"
            elif current_measurement == "11":
                new_case = "-11"
        elif prev_case == "-01":
            if current_measurement == "00":
                new_case = "-01"
            elif current_measurement == "01":
                new_case = "-00"
            elif current_measurement == "10":
                new_case = "11"
            elif current_measurement == "11":
                new_case = "10"
        elif prev_case == "-10":
            if current_measurement == "00":
                new_case = "-10"
            elif current_measurement == "01":
                new_case = "-11"
            elif current_measurement == "10":
                new_case = "-00"
            elif current_measurement == "11":
                new_case = "-01"
        elif prev_case == "-11":
            if current_measurement == "00":
                new_case = "-11"
            elif current_measurement == "01":
                new_case = "-10"
            elif current_measurement == "10":
                new_case = "01"
            elif current_measurement == "11":
                new_case = "00"
        return new_case
    
    @staticmethod
    def count_node_occurrences(request: List[Tuple[str]], node_name: str):
        count = 0
        for pair in request:
            count += pair.count(node_name)
        return count