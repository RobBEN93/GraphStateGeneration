def gen_star_graph(self, context: ProgramContext, center_node: str, leaves: list):
    """
    Generate a star-shaped graph state, with one center node and multiple leaves.
    This involves creating EPR pairs between the center and each leaf, and then
    performing operations (H, X, Z) based on measurement outcomes to merge them into a graph state.

    :param context: ProgramContext containing sockets and connections.
    :param center_node: The central node of the star graph.
    :param leaves: A list of leaf nodes that will be connected to the center node.
    """
    
    counter = 0

    # Generate EPR pairs from center_node to each leaf and merge qubits at center node
    for node in leaves:
        # For each leaf:
        # 1. Find the shortest path from center_node to the leaf.
        # 2. Distribute an EPR pair along that path.
        # 3. If first iteration, label the qubit at center_node as "center_qubit".
        path = shortest_path(self.G, (center_node, node))
        
        if counter == 0:
            result = yield from self.arbitrary_node_epr_pair(context, path, qubit_start="center_qubit")
        else:
            result = yield from self.arbitrary_node_epr_pair(context, path)
        
        # If this node ends up holding the leaf’s EPR qubit
        if hasattr(self, 'epr_qubit_0') and result == self.epr_qubit_0:
            # Leaf node operations
            if counter == 0:
                # First leaf just establishes a Bell pair with center node
                print(f"[Leaf {self.node_name}] Step 0: Established an EPR pair with center {center_node}.")
                yield from context.connection.flush()
                counter += 1
            
            elif counter == 1:
                # Second leaf: integrate into a three-node graph state
                msg = yield from self.send_msg_to_dist_node(context, path)
                print(f"[Leaf {self.node_name}] Step {counter}: EPR pair established with {center_node}. Received measurement outcome '{msg}' from center.")
                
                if msg == "0":
                    print(f"[Leaf {self.node_name}] Applying H gate (measurement was 0). Now forming a three-node graph state.")
                    self.epr_qubit_0.H()
                else:
                    print(f"[Leaf {self.node_name}] Applying X then H gate (measurement was 1). Correcting and forming a three-node graph state.")
                    self.epr_qubit_0.X()
                    self.epr_qubit_0.H()
                
                yield from context.connection.flush()
                counter += 1
            
            else:
                # Additional leaves beyond the second
                print(f"[Leaf {self.node_name}] Step {counter}: Another EPR pair with {center_node} established. Integrating into the growing star graph.")
                yield from context.connection.flush()
                counter += 1
        
        # If this node has 'center_qubit', it means it's the center node performing operations
        elif hasattr(self, 'center_qubit'):
            # Center node operations
            print(f"[Center {self.node_name}] Step {counter}: Sharing an EPR pair with leaf {node}.")
            
            if counter == 0:
                # Just formed the first Bell pair, no corrections needed yet
                yield from context.connection.flush()
                counter += 1
            
            elif counter == 1:
                # Merging the second leaf to form a three-node state
                self.center_qubit.cnot(self.epr_qubit_1)
                r_1 = self.epr_qubit_1.measure()
                yield from context.connection.flush()
                print(f"[Center {self.node_name}] Measured qubit (result {r_1}). Sending measurement outcome to leaf {path[-1]} for correction.")
                yield from self.send_msg_to_dist_node(context, path, str(r_1))
                counter += 1
                print(f"[Center {self.node_name}] Step {counter - 1} complete: Merged the second node. Currently forming a 3-node graph.")
            
            else:
                # Adding more leaves beyond the second
                print(f"[Center {self.node_name}] Step {counter}: Integrating another leaf {node} into the star graph.")
                
                # Create an auxiliary qubit and use it for entanglement swapping
                local_qubit = Qubit(context.connection)
                local_qubit.H()
                self.epr_qubit_1.H()
                local_qubit.cphase(self.epr_qubit_1)
                self.center_qubit.cphase(local_qubit)
                
                measurement1 = measXY(local_qubit, angle=np.pi/2)
                measurement2 = measXY(self.epr_qubit_1, angle=np.pi/2)
                
                yield from context.connection.flush()
                counter += 1
                print(f"[Center {self.node_name}] Step {counter - 1} complete: Successfully integrated leaf {node}. Star graph now includes {counter + 1} nodes.")
        
        else:
            # If the node is neither a leaf currently holding epr_qubit_0 nor the center
            # This might happen if the current node is an intermediate node in the path.
            # Just acknowledge the step and move on.
            print(f"[Node {self.node_name}] Step {counter}: Intermediate node in EPR distribution path.")
            
            if counter == 0:
                yield from context.connection.flush()
                counter += 1
            elif counter == 1:
                yield from self.send_msg_to_dist_node(context, path)
                counter += 1
            else:
                yield from context.connection.flush()
                counter += 1
