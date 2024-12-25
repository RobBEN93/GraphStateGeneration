from typing import Optional, List, Tuple
import numpy as np

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from netqasm.sdk.qubit import Qubit

from squidasm.sim.stack.common import LogManager

from squidasm.util.routines import measXY

from yaml_to_nx import shortest_path

import netsquid as ns

#Examples provided
example_path = ['node_0','node_1','node_2','node_3','node_4','node_8']
example_path2 = ['node_0','node_1','node_2']

leaves = ["node_9","node_3","node_8","node_1","node_5","node_6","node_7","node_4"]

class GraphStateDistribution(Program):
    
    def __init__(self, node_name: str, peer_names: list, graph):
        """
        Initialize the GraphStateDistribution object.

        :param node_name: Name of the current node in the quantum network.
        :param peer_names: List of all the peer node names (neighbors) that this node is directly connected to.
        :param graph: A networkx graph structure representing the topology of the quantum network.
        """
        
        self.node_name = node_name
        self.peer_names = peer_names
        self.G = graph
        
        # Create attributes for classical and EPR sockets dynamically based on peer names.
        for peer in peer_names:
            setattr(self,f"csocket_{peer}", None)
            setattr(self,f"epr_socket_{peer}", None)
      
        # Initialize logger for this node
        self.logger = LogManager.get_stack_logger(f"{self.node_name} program")

    @property
    def meta(self) -> ProgramMeta:

        return ProgramMeta(
            name=f"graph_state_generation_at_{self.node_name}",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=4,
        )

    def run(self, context: ProgramContext):
        """
        The main entry point for the program's execution on a given node.
        
        In this demostration his method:
        - Sets up sockets.
        - Generates a star graph state from the example leaves

        :param context: ProgramContext provided by the runtime, containing sockets and other runtime info.
        :return: A dictionary (empty by default) to store any results or metadata from the run. Can return sim results such as sim time
        """
        logger = self.logger
        logger.info(f"{self.node_name}")

        self.setup_sockets(context)
        run_time = ns.sim_time()
        #print(f"{self.node_name} has peers: {self.peer_names}")
        
        yield from self.gen_star_graph2(context,"node_0",leaves)
        
        #short = shortest_path(self.G, ("node_1", self.node_name))
        #print(f"{self.node_name} has shortest path with node_1: {short}")
        #yield from self.arbitrary_node_epr_pair(context,path=["node_1","node_0"],apply_correction=True)

        return {} 
    

    def gen_star_graph2(self, context: ProgramContext, center_node: str, leaves: list):
        
        all_sync_paths = []
        for sync_node in self.G.nodes():
            if sync_node != center_node:
                sync_path = shortest_path(self.G,(center_node,sync_node))
                all_sync_paths.append(sync_path)
        
        counter = 0
        
        for node in leaves:
            
            path = shortest_path(self.G,(center_node, node))

            if self.node_name == center_node:
                #print(f"CENTER NODE counter: {counter}")
                if counter == 0:
                    print(f"{ns.sim_time()}:[Center {self.node_name}] Step {counter}: Integrating leaf {node} into the star graph.")
                    yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                elif counter == 1:
                    print(f"{ns.sim_time()}:[Center {self.node_name}] Step {counter}: Integrating leaf {node} into the star graph.")
                    yield from self.arbitrary_node_epr_pair(context,path)
                    self.center_qubit.cnot(self.epr_qubit_1)
                    r_1 = self.epr_qubit_1.measure()
                    yield from context.connection.flush()
                    print(f"{ns.sim_time()}:[Center {self.node_name}] Step 1: Measured qubit (result {r_1}). Sending measurement outcome to leaf {path[-1]} for correction.")
                    yield from self.send_msg_to_dist_node(context,path,str(r_1))
                    print(f"{ns.sim_time()}:---------[Center {self.node_name}] Step 1 complete: Merged the second leaf. Currently forming a 3-node graph.")
                elif counter > 1:
                    print(f"{ns.sim_time()}:[Center {self.node_name}] Step {counter}: Integrating leaf {node} into the star graph.")
                    yield from self.arbitrary_node_epr_pair(context,path)
                    print(f"{ns.sim_time()}:[Center {self.node_name}] Step {counter}: Integrating leaf {node} into the star graph.------------------------")
                    local_qubit = Qubit(context.connection) # We generate an auxiliary qubit to perform entanglement swapping with the current center of the graph state
                    local_qubit.H() # Perform an H gate to produce a |+> state
                    self.epr_qubit_1.H() # self.epr_qubit_1 is part of a |phi+> state with current node from leaves. Apply H gate to produce a graph state CZ|+>|+>
                    local_qubit.cphase(self.epr_qubit_1) # Add an edge from the auxiliary qubit to the pair from the leaf
                    self.center_qubit.cphase(local_qubit) # Add an edge from the center qubit to the auxiliary qubit
                    
                    # Perform entanglement swapping via measurement in the Y basis
                    measXY(local_qubit,angle=np.pi/2)
                    measXY(self.epr_qubit_1,angle=np.pi/2)
                    
                    yield from context.connection.flush()
                    
                    print(f"{ns.sim_time()}:---------[Center {self.node_name}] Step {counter} complete: Successfully integrated leaf {node}. Star graph now includes {counter + 1} leaves.")
                
                for sync_path in all_sync_paths:
                    yield from self.send_msg_to_dist_node(context, sync_path, "confirm")
                for sync_path in all_sync_paths:
                    yield from self.send_msg_to_dist_node(context, sync_path)
                #print(f"######################{ns.sim_time()}: CENTER {self.node_name} has synced at step {counter}")
                counter += 1
            
            elif self.node_name in leaves:
                if self.node_name in path:
                    if self.node_name == node:
                        #print(f"{self.node_name} CURRENT LEAF counter {counter}")
                        if counter == 0:
                            yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                            print(f"{ns.sim_time()}:[Leaf {self.node_name}] Step 0: Established an EPR pair with center {center_node}.")
                            
                        elif counter == 1:
                            yield from self.arbitrary_node_epr_pair(context,path)
                            print(f"{ns.sim_time()}:[Leaf {self.node_name}] Step 1: Established an EPR pair with center {center_node}.")
                            msg = yield from self.send_msg_to_dist_node(context,path)
                            print(f"{ns.sim_time()}:[Leaf {self.node_name}] Step {counter}: EPR pair established with {center_node}. Received measurement outcome '{msg}' from center.")
                            if msg == "0":
                                print(f"{ns.sim_time()}:[Leaf {self.node_name}] received measurement 0 applies H gate to produce three node graph state.")
                                self.epr_qubit_0.H()
                            else:
                                print(f"{ns.sim_time()}:[Leaf {self.node_name}] received measurement 1 applies correction X and then H gate to produce three node graph state.")
                                self.epr_qubit_0.X()
                                self.epr_qubit_0.H()
                            yield from context.connection.flush()

                        elif counter > 1:
                            yield from self.arbitrary_node_epr_pair(context,path)
                            print(f"{ns.sim_time()}:[Leaf {self.node_name}] Step {counter}: Established an EPR pair with center {center_node}.")
                        
                        for sync_path in all_sync_paths:
                            yield from self.send_msg_to_dist_node(context, sync_path)
                        for sync_path in all_sync_paths:
                            yield from self.send_msg_to_dist_node(context, sync_path,"confirm")
                        #print(f"######################{ns.sim_time()}: {self.node_name} has synced at step {counter}")
                        counter += 1
                    else:
                        #print(f"{self.node_name} NOT CURRENT LEAF, IN PATH for node {node} counter {counter}")
                        if counter == 0:
                            yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                        elif counter == 1:
                            yield from self.arbitrary_node_epr_pair(context,path)
                            yield from self.send_msg_to_dist_node(context,path)
                        elif counter > 1:
                            yield from self.arbitrary_node_epr_pair(context,path)
                        
                        for sync_path in all_sync_paths:
                            yield from self.send_msg_to_dist_node(context, sync_path)
                        for sync_path in all_sync_paths:
                            yield from self.send_msg_to_dist_node(context, sync_path)
                        #print(f"######################{ns.sim_time()}: {self.node_name} has synced at step {counter}")
                        counter += 1
                else:
                    #print(f"{self.node_name} NOT CURRENT LEAF, NOT IN PATH for node {node} counter {counter}")
                    if counter == 0:
                        yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                    elif counter == 1:
                        yield from self.arbitrary_node_epr_pair(context,path)
                        yield from self.send_msg_to_dist_node(context,path)
                    elif counter > 1:
                        yield from self.arbitrary_node_epr_pair(context,path)
                        
                    for sync_path in all_sync_paths:
                        yield from self.send_msg_to_dist_node(context, sync_path)
                    for sync_path in all_sync_paths:
                        yield from self.send_msg_to_dist_node(context, sync_path)
                    #print(f"######################{ns.sim_time()}: {self.node_name} has synced at step {counter}")
                    counter += 1
            
            elif self.node_name not in leaves:
                if self.node_name in path:
                    #print(f"{self.node_name} NOT LEAF, IN PATH for node {node} counter {counter}")
                    if counter == 0:
                        yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                    elif counter == 1:
                        yield from self.arbitrary_node_epr_pair(context,path)
                        yield from self.send_msg_to_dist_node(context,path)
                    elif counter > 1:
                        yield from self.arbitrary_node_epr_pair(context,path)
                        
                    for sync_path in all_sync_paths:
                        yield from self.send_msg_to_dist_node(context, sync_path)
                    for sync_path in all_sync_paths:
                        yield from self.send_msg_to_dist_node(context, sync_path)
                    #print(f"######################{ns.sim_time()}: {self.node_name} has synced at step {counter}")
                    counter += 1
                else:
                    #print(f"{self.node_name} NOT LEAF, NOT IN PATH for node {node} counter {counter}")
                    if counter == 0:
                        yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                    elif counter == 1:
                        yield from self.arbitrary_node_epr_pair(context,path)
                        yield from self.send_msg_to_dist_node(context,path)
                    elif counter > 1:
                        yield from self.arbitrary_node_epr_pair(context,path)
                    
                    for sync_path in all_sync_paths:
                        yield from self.send_msg_to_dist_node(context, sync_path)
                    for sync_path in all_sync_paths:
                        yield from self.send_msg_to_dist_node(context, sync_path)
                    #print(f"######################{ns.sim_time()}: {self.node_name} has synced at step {counter}")
                    counter += 1

    def gen_star_graph(self, context: ProgramContext, center_node: str, leaves: list):
        """
        Generate a star-shaped graph state, with one center node and multiple leaves.

        The routine attempts to build the star state by creating EPR pairs along shortest paths from the center
        node to each leaf and then applying necessary gates (H, X, Z) depending on measurement outcomes.

        :param context: ProgramContext containing sockets and connections.
        :param center_node: The central node of the star graph.
        :param leaves: A list of leaf nodes that will be connected to the center node.
        
        Notice that generating a star graph can also be easily achieved by generating a GHZ state and then applying a 
        Hadamard gate to qubit at the desired center. In such case we could use the create_ghz method provided by the
        squidasm routine, however in this case we allow for connection over distant nodes, wheras the method requires
        EPR sockets between the participating nodes
        """
        
        counter = 0 # A counter is defined so that each node's operation properly aligns with each step
        
        # Generate EPR pairs from center_node to each node in leaf, and merge qubits at center node
        for node in leaves:
            
            # For each leaf:
            # 1. Find the shortest path from center_node to the leaf.
            # 2. Distribute an EPR pair along that path.
            # Save qubit from the first EPR pair from center node as center_qubit
            # For center_node - node in leaves, ´result´ are end qubits from the arbitrary_node_epr_pair method. Nodes that aren't end nodes produce result = 0
            path = shortest_path(self.G,(center_node, node))
            if counter == 0:
                
                # First iteration defines the center_qubit label in arbitrary_node_epr_pair
                result = yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
            
            else:
                # Subsequent leaves use default labeling
                result = yield from self.arbitrary_node_epr_pair(context,path)

            # epr_qubit_0 is the label for qubits at end nodes from EPR generation which corresponds to leaves in this case
            if hasattr(self, 'epr_qubit_0') and result == self.epr_qubit_0:
                
                # At step 0 the first leaf just produces a Bell pair
                if counter == 0:
                    print(f"[Leaf {self.node_name}] Step 0: Established an EPR pair with center {center_node}.")
                    yield from context.connection.flush()
                    counter += 1
                
                # At step 1 (second leaf): perform a protocol to merge the second and first step Bells pair into a three-node graph state.
                # This involves receiving a measurement result from the center node and applying corrections.
                elif counter == 1:
                    msg = yield from self.send_msg_to_dist_node(context,path)
                    print(f"[Leaf {self.node_name}] Step {counter}: EPR pair established with {center_node}. Received measurement outcome '{msg}' from center.")
                    if msg == "0":
                        print(f"[Leaf {self.node_name}] received measurement 0 applies H gate to produce three node graph state")
                        self.epr_qubit_0.H()
                    else:
                        print(f"[Leaf {self.node_name}] received measurement 1 applies correction X and then H gate to produce three node graph state")
                        self.epr_qubit_0.X()
                        self.epr_qubit_0.H()
                    yield from context.connection.flush()
                    
                    counter += 1
                    
                if counter > 1:
                    # For subsequent leaves, the process can be generalized and extended.
                    # The leaves keep receiving EPR pairs from center_node
                    # The states from the leaves are transformed into CZ|+>|+> and merged into the first state from that center node
                    print(f"[Leaf {self.node_name}] Step {counter}: Next EPR pair with {center_node} established. Integrating into star graph.")
                    yield from context.connection.flush()
                    counter += 1
            
            # Identifies center node
            elif hasattr(self,'center_qubit'):
                print(f"[Center {self.node_name}] Step {counter}: Shares EPR pair with leaf {node}.")
                if counter == 0:
                    # First step only generates the first Bell pair
                    yield from context.connection.flush()
                    counter += 1
                
                elif counter == 1:
                    # Second step performs a protocol that produces a three node graph state with center at center_qubit
                    # sends result to second leaf for correction
                    self.center_qubit.cnot(self.epr_qubit_1)
                    r_1 = self.epr_qubit_1.measure()
                    yield from context.connection.flush()
                    print(f"[Center {self.node_name}] Measured qubit (result {r_1}). Sending measurement outcome to leaf {path[-1]} for correction.")
                    yield from self.send_msg_to_dist_node(context,path,str(r_1))
                    counter += 1
                    print(f"[Center {self.node_name}] Step {counter - 1} complete: Merged the second node. Currently forming a 3-node graph.")
            
                elif counter > 1:
                    print(f"[Center {self.node_name}] Step {counter}: Integrating another leaf {node} into the star graph.")
                    
                    # For more leaves:
                    # We have a center_node connected to n leaves, n>1
                    # To this point we already have the next Bell pair with center node and the n+1 leaf
                    # Take that pair and transform it into a graph state CZ|+>|+> by applying H gate to either qubit (epr_qubit_1 in this case)
                    # Take a new qubit (local qubit) and perform H gate to generate a |+> state
                    # Perform CZ gates between center qubit and new qubit, and new qubit and epr qubit
                    # Perform a Y measurement to effectively swap the entanglement and have the center qubit entangled with the new leaf
                    # Obtain measurements to perform correction (not yet implemented)
                    
                    local_qubit = Qubit(context.connection) # We generate an auxiliary qubit to perform entanglement swapping with the current center of the graph state
                    local_qubit.H() # Perform an H gate to produce a |+> state
                    self.epr_qubit_1.H() # self.epr_qubit_1 is part of a |phi+> state with current node from leaves. Apply H gate to produce a graph state CZ|+>|+>
                    local_qubit.cphase(self.epr_qubit_1) # Add an edge from the auxiliary qubit to the pair from the leaf
                    self.center_qubit.cphase(local_qubit) # Add an edge from the center qubit to the auxiliary qubit
                    
                    # Perform entanglement swapping via measurement in the Y basis
                    measurement1 = measXY(local_qubit,angle=np.pi/2)
                    measurement2 = measXY(self.epr_qubit_1,angle=np.pi/2)
                    
                    yield from context.connection.flush()
                    counter += 1
                    print(f"---------[Center {self.node_name}] Step {counter - 1} complete: Successfully integrated leaf {node}. Star graph now includes {counter + 1} nodes.")

            elif counter == 0:
                #print(f"[Node {self.node_name}] Step {counter}: Intermediate node in EPR distribution path.")
                yield from context.connection.flush()
                counter += 1
                
            elif counter == 1 :
                #print(f"[Node {self.node_name}] Step {counter}: Intermediate node in EPR distribution path.")
                yield from self.send_msg_to_dist_node(context,path)
                counter += 1
                
            elif counter > 1:
                #print(f"[Node {self.node_name}] Step {counter}: Intermediate node in EPR distribution path.")
                yield from context.connection.flush()
                counter += 1
                
            #print(f"{self.node_name} produces result: {result} from epr pair generation at step {counter}")
            
    def send_msg_to_dist_node(self, context: ProgramContext, path: List, message: Optional[str] = None):
        """
        Transmit a message along a given path of nodes.

        The message is handed off hop-by-hop until it reaches the end node in the path.
        If this node is the start of the path, it sends the message to the next node.
        If intermediate, it passes along the message it receives from the previous node.
        If at the end, it returns the received message.

        :param context: ProgramContext for connections.
        :param path: List of nodes forming a path from a start to an end node.
        :param message: The message to send if this node is at the start of the path.
        :return: The message received if this node is at the end of the path, else 0.
        """
        
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

                
    def setup_sockets(self, context: ProgramContext):
        """
        Setup classical and EPR sockets for this node using the provided ProgramContext.

        :param context: ProgramContext from the runtime.
        """
        for peer in self.peer_names:
            setattr(self,f"csocket_{peer}", context.csockets[peer])
            setattr(self,f"epr_socket_{peer}", context.epr_sockets[peer])
    
    def adjacent_node_epr_pair(self, context: ProgramContext, node1: str, node2: str, qubit_start="epr_qubit_1", qubit_end="epr_qubit_0"):
        """
        This function establishes a Bell pair between two adjacent nodes, node1 and node2.

        If node is node1:
            - Create an EPR pair and store it in qubit_start attribute.
        If node is node2:
            - Receive the EPR pair and store it in qubit_end attribute.

        :param context: ProgramContext for connections.
        :param node1: The starting node of the EPR pair.
        :param node2: The ending node of the EPR pair.
        :param qubit_start: Attribute name for storing the qubit on the start node.
        :param qubit_end: Attribute name for storing the qubit on the end node.
        :return: The qubit attribute set on this node if involved, else 0.
        """
        # Check if this node is one of the specified nodes
        if self.node_name in [node1, node2]:

            if self.node_name == node1:
                epr_socket_next = getattr(self, f"epr_socket_{node2}")
                qubit = epr_socket_next.create_keep()[0]
                setattr(self, qubit_start, qubit)  # set the qubit to the specified attribute
                self.logger.info(f"{self.node_name} creates EPR pair and sends it to {node2}")
                print(f"{ns.sim_time()}: {self.node_name} creates EPR pair and sends it to {node2}")
                attribute = getattr(self,qubit_start)
                return attribute
                
            elif self.node_name == node2:
                epr_socket_prev = getattr(self, f"epr_socket_{node1}")
                qubit = epr_socket_prev.recv_keep()[0]
                setattr(self, qubit_end, qubit)
                self.logger.info(f"{self.node_name} receives EPR pair from {node1}")
                print(f"{ns.sim_time()}: {self.node_name} receives EPR pair from {node1}")
                attribute = getattr(self,qubit_end)
                return attribute

        else:
            # This node is not involved in the pair creation, just flush
            yield from context.connection.flush()
        
        #print(f"{self.node_name} is not involved in the Bell pair creation between {node1} and {node2}")
    
    def arbitrary_node_epr_pair(self, context: ProgramContext, path: List, apply_correction: bool = True, 
                                qubit_start="epr_qubit_1", qubit_end="epr_qubit_0"):
        
        """
        Distribute an EPR pair between the first and last nodes in the given path using a chain of entanglement swaps.

        Steps:
        1. Create adjacent EPR pairs along the path.
        2. Perform entanglement swapping at intermediate nodes.
        3. Communicate classical measurement results along the path to ensure end node knows the final "case" and returns it to start node.
        4. If apply_correction is True, the end nodes apply the necessary Pauli corrections to ensure a |phi+> state.

        :param context: ProgramContext for connections.
        :param path: The list of nodes forming a linear chain from start to end.
        :param apply_correction: Whether to apply final corrections to ensure a canonical Bell state.
        :param qubit_start: Attribute name to store the qubit at the start node.
        :param qubit_end: Attribute name to store the qubit at the end node.
        :return: The final qubit at either the start or end node after entanglement swapping and corrections.
        
        Bell measurements and states are tracked on each node so that only the end nodes apply operations:

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
        if len(path) == 2:
            result = yield from self.adjacent_node_epr_pair(context,path[0],path[1],qubit_start,qubit_end)
            return result

        # Establish EPR pairs along connected nodes on the path
        if self.node_name in path:
            self.current_index = path.index(self.node_name)
            if self.node_name == path[0]:
                epr_socket_next = getattr(self, f"epr_socket_{path[1]}")
                csocket_next = getattr(self, f"csocket_{path[1]}")
                qubit = epr_socket_next.create_keep()[0]
                setattr(self, qubit_start, qubit)  # set the qubit to the specified attribute
                self.logger.info(f"[{path[0]}-EPR chain-{path[-1]}]{self.node_name} creates EPR pair and sends it to {path[1]}")
                #print(f"[{path[0]}-EPR chain-{path[-1]}]{self.node_name} creates EPR pair and sends it to {path[1]}")
                
            elif self.node_name != path[-1]:
                epr_socket_prev = getattr(self, f"epr_socket_{path[self.current_index-1]}")
                csocket_prev = getattr(self, f"csocket_{path[self.current_index-1]}")
                aux_epr_qubit_0 = epr_socket_prev.recv_keep()[0]
                self.logger.info(f"[{path[0]}-EPR chain-{path[-1]}]{self.node_name} receives EPR pair from {path[self.current_index-1]}")
                #print(f"[{path[0]}-EPR chain-{path[-1]}]{self.node_name} receives EPR pair from {path[self.current_index-1]}")
                
                epr_socket_next = getattr(self, f"epr_socket_{path[self.current_index+1]}")
                csocket_next = getattr(self, f"csocket_{path[self.current_index+1]}")
                aux_epr_qubit_1 = epr_socket_next.create_keep()[0]
                self.logger.info(f"[{path[0]}-EPR chain-{path[-1]}]{self.node_name} creates EPR pair and sends it to {path[self.current_index+1]}")
                #print(f"[{path[0]}-EPR chain-{path[-1]}]{self.node_name} creates EPR pair and sends it to {path[self.current_index+1]}")

            else:
                epr_socket_prev = getattr(self, f"epr_socket_{path[self.current_index-1]}")
                csocket_prev = getattr(self, f"csocket_{path[self.current_index-1]}")
                qubit = epr_socket_prev.recv_keep()[0]
                setattr(self, qubit_end, qubit)  # set the qubit to the specified attribute
                self.logger.info(f"[{path[0]}-EPR chain-{path[-1]}]{self.node_name} receives EPR pair from {path[self.current_index-1]}")
                #print(f"[{path[0]}-EPR chain-{path[-1]}]{self.node_name} receives EPR pair from {path[self.current_index-1]}")
        else:
            yield from context.connection.flush()
        
        # Perform chain of entanglement swapping
        if self.node_name in path:
            
            if self.node_name == path[1]:
                
                # Second node in the chain performs the first Bell measurement and sends result to next node
                aux_epr_qubit_0.cnot(aux_epr_qubit_1)
                aux_epr_qubit_0.H()
                r0 = aux_epr_qubit_0.measure()
                r1 = aux_epr_qubit_1.measure()
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
                    aux_epr_qubit_0.cnot(aux_epr_qubit_1)
                    aux_epr_qubit_0.H()
                    r0 = aux_epr_qubit_0.measure()
                    r1 = aux_epr_qubit_1.measure()
                    
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
                        yield from self.apply_swap_correction(context,current_case,"end",qubit=qubit_end)
                        # Confirm correction
                        yield from self.send_msg_to_dist_node(context,path)
                        end_node_qubit = getattr(self,qubit_end)
                        self.logger.info(f"{self.node_name} receives EPR pair from {path[0]}")
                        print(f"{ns.sim_time()}:{self.node_name} receives EPR pair from {path[0]}")
                        return end_node_qubit
                    else:
                        end_node_qubit = getattr(self,qubit_end)
                        return end_node_qubit, current_case
                
                elif self.node_name == path[0]:
                    # First node does not perform any operation after generating its EPR pair with the following node
                    # except when apply_correction is selected, in which case it waits for the information on the needed
                    # Pauli operations
                    if apply_correction:
                        msg = yield from self.send_msg_to_dist_node(context,list(reversed(path)))

                        yield from self.apply_swap_correction(context,msg,"start",qubit=qubit_start)
                        # Confirm correction
                        yield from self.send_msg_to_dist_node(context,path,"confirmation")
                        start_node_qubit = getattr(self,qubit_start)
                        self.logger.info(f"{self.node_name} creates EPR pair and sends it to {path[-1]}")
                        print(f"{ns.sim_time()}:{self.node_name} creates EPR pair and sends it to {path[-1]}")
                        return start_node_qubit
                    
                    else:
                        start_node_qubit = getattr(self,qubit_start)
                        return start_node_qubit
        else:
            # If not on the path, just flush
            yield from context.connection.flush()
        
        return 0
    
    def apply_swap_correction(self, context: ProgramContext, case, node, qubit= None):
        """
        Apply necessary corrections on the final qubit based on the case string.
        The 'case' determines what Bell state (or sign-flipped Bell state) the final qubit corresponds to.

        Cases:
        '00', '01', '10', '11' and their negative counterparts '-00', '-01', '-10', '-11' represent different
        Bell states. We apply Pauli X, Z, or combinations thereof to correct the state to a known canonical form.

        :param context: ProgramContext for connections.
        :param case: The final case string describing the Bell state variant.
        :param node: 'end' if this node is the last node in the path, 'start' if it is the first.
        """
        # Corrections differ depending on whether this is the start or the end node.
        # The logic below matches each case to the required correction operations.
        if node == "end":
            if qubit is None:
                end_node_qubit=getattr(self,"epr_qubit_0")
            else:
                end_node_qubit=getattr(self,qubit)
            if case == "00":
                self.logger.info(f"State is |phi+>. No correction needed for {self.node_name}.")
                print((f"State is |phi+>. No correction needed for {self.node_name}."))
            elif case == "01":
                self.logger.info(f"State is |psi+>. Applying Pauli-X correction at {self.node_name}.")
                print(f"State is |psi+>. applying Pauli-X correction at {self.node_name}.")
                end_node_qubit.X()
            elif case == "10":
                self.logger.info(f"State is |phi->. Applying Pauli-Z correction at {self.node_name}.")
                print(f"State is |phi->. Applying Pauli-Z correction at {self.node_name}.")
                end_node_qubit.Z()
            elif case == "11":
                self.logger.info(f"State is |psi->. Applying Pauli-X and Pauli-Z correction at {self.node_name}.")
                print(f"State is |psi->. applying Pauli-X and Pauli-Z correction at {self.node_name}.")
                end_node_qubit.X()
                end_node_qubit.Z()
            elif case == "-00":
                self.logger.info(f"State is -|phi+>. Applying XZX correction at {self.node_name}.")
                print((f"State is -|phi+>. Applying XZX correction at {self.node_name}."))
                end_node_qubit.X()
                end_node_qubit.Z()
                end_node_qubit.X()
            elif case == "-01":
                self.logger.info(f"State is -|psi+>. Applying XZ correction at {self.node_name}.")
                print(f"State is -|psi+>. Applying XZ correction at {self.node_name}.")
                end_node_qubit.Z()
                end_node_qubit.X()
            elif case == "-10":
                self.logger.info(f"State is -|phi->. Applying ZX correction at {self.node_name}.")
                print(f"State is -|phi->. Applying ZX correction at {self.node_name}.")
                end_node_qubit.X()
                end_node_qubit.Z()
            elif case == "-11":
                self.logger.info(f"State is -|psi->. Applying XZ correction at {self.node_name}.")
                print(f"State is -|psi->. Applying XZ correction at {self.node_name}.")
                end_node_qubit.Z()
                end_node_qubit.X()
        if node == "start":
            if qubit is None:
                start_node_qubit=getattr(self,"epr_qubit_1")
            else:
                start_node_qubit=getattr(self,qubit)
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
                start_node_qubit.Z()
            elif case == "-01":
                self.logger.info(f"State is -|psi+>. Applying Pauli-Z correction at {self.node_name}.")
                print(f"State is -|psi+>. Applying Pauli-Z correction at {self.node_name}.")
                start_node_qubit.Z()
            elif case == "-10":
                self.logger.info(f"State is -|phi->. Applying Pauli-X correction at {self.node_name}.")
                print(f"State is -|phi->. Applying Pauli-X correction at {self.node_name}.")
                start_node_qubit.X()
            elif case == "-11":
                self.logger.info(f"State is -|psi->.  No correction needed for {self.node_name}.")
                print(f"State is -|psi->. No correction needed for {self.node_name}.")
        yield from context.connection.flush()

    def broadcast_message(self, context: ProgramContext, sending_node: str, message: str):
        for node in self.G.nodes():
            if node != sending_node:
                path = shortest_path(self.G,(sending_node,node))
                yield from self.send_msg_to_dist_node(context, path)
        return 1
    
    @staticmethod
    def check_case(prev_case, current_measurement):
        """
        Determine the new case based on the previous case and the current measurement result.

        This function maps the measurement results of intermediate entanglement swaps to a new 'case'
        indicating which Bell state variant the end-to-end entangled state is currently in.
        
        The logic encodes transitions between cases depending on measurement outcomes, ensuring the correct
        final corrections can be applied at the end nodes.

        :param prev_case: The previous case string before this entanglement swap.
        :param current_measurement: The measurement results from the current node, e.g., "00", "01", "10", or "11".
        :return: The new case string after applying the logic of how states transform through entanglement swapping.
        """
        # The mapping is based on transformations of Bell states through consecutive Bell measurements.
        # Each case combination leads to a deterministic new case (including sign changes indicated by "-")
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
        """
        Count how many times a particular node appears in a request list.
        :param request: A list of (node_i, node_j) tuples indicating edges graph state generation.
        :param node_name: The node name to count.
        :return: The number of occurrences of node_name in the request.
        """
        return sum([edge.count(node_name) for edge in request])