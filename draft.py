def broadcast_message(self, context: ProgramContext, sending_node: str, message: str)
    for node in self.G.nodes():
        if node != sending_node:
            path = shortest_path(self.G,(sending_node,node))
            yield from self.send_msg_to_dist_node(context, path, message)

def gen_star_graph2(self, context: ProgramContext, center_node: str, leaves: list):

        counter = 0
        
        for node in leaves:
            
            path = shortest_path(self.G,(center_node, node))
            
            if self.node_name == center_node:
                if counter == 0:
                    yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                elif counter == 1:
                    yield from self.arbitrary_node_epr_pair(context,path)
                    self.center_qubit.cnot(self.epr_qubit_1)
                    r_1 = self.epr_qubit_1.measure()
                    yield from context.connection.flush()
                    print(f"[Center {self.node_name}] Measured qubit (result {r_1}). Sending measurement outcome to leaf {path[-1]} for correction.")
                    yield from self.send_msg_to_dist_node(context,path,str(r_1))
                    counter += 1
                    print(f"[Center {self.node_name}] Step {counter - 1} complete: Merged the second node. Currently forming a 3-node graph.")
                elif counter > 1:
                    print("something")
                counter += 1
                
            elif self.node_name in leaves:
                if self.node_name in path:
                    if self.node_name == node:
                        if counter == 0:
                            yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                            print(f"[Leaf {self.node_name}] Step 0: Established an EPR pair with center {center_node}.")
                            
                        elif counter == 1:
                            yield from self.arbitrary_node_epr_pair(context,path)
                            print(f"[Leaf {self.node_name}] Step 1: Established an EPR pair with center {center_node}.")
                            msg = yield from self.send_msg_to_dist_node(context,path)
                            print(f"[Leaf {self.node_name}] Step {counter}: EPR pair established with {center_node}. Received measurement outcome '{msg}' from center.")
                            if msg == "0":
                                print(f"[Leaf {self.node_name}] received measurement 0 applies H gate to produce three node graph state.")
                                self.epr_qubit_0.H()
                            else:
                                print(f"[Leaf {self.node_name}] received measurement 1 applies correction X and then H gate to produce three node graph state.")
                                self.epr_qubit_0.X()
                                self.epr_qubit_0.H()
                            yield from context.connection.flush()

                        elif counter > 1:
                            print("something")
                        counter += 1
                    else:
                        if counter == 0:
                            yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                        elif counter == 1:
                            yield from self.arbitrary_node_epr_pair(context,path)
                            yield from self.send_msg_to_dist_node(context,path)
                        elif counter > 1:
                            print("something")
                        counter += 1
                        
            elif self.node_name not in leaves:
                if self.node_name in path:
                    if counter == 0:
                        yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
                    elif counter == 1:
                        yield from self.arbitrary_node_epr_pair(context,path)
                        yield from self.send_msg_to_dist_node(context,path)
                    elif counter > 1:
                        print("something")
                    counter += 1
                else:
                    yield from context.connection.flush()
            
            
            yield from self.arbitrary_node_epr_pair(context,path,qubit_start="center_qubit")
            
            if self.node_name == node:
                print(f"[Leaf {self.node_name}] Step 0: Established an EPR pair with center {center_node}.")
                yield from context.connection.flush()
                
                if counter == 1:
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
                    print(f"[Leaf {self.node_name}] Step {counter}: Next EPR pair with {center_node} established. Integrating into star graph.")
                    yield from context.connection.flush()
                    counter += 1
            
            if self.node_name == center_node:
                                
                if counter == 0:
                    yield from context.connection.flush()
                    counter += 1
                
                elif counter == 1:
                    self.center_qubit.cnot(self.epr_qubit_1)
                    r_1 = self.epr_qubit_1.measure()
                    yield from context.connection.flush()
                    print(f"[Center {self.node_name}] Measured qubit (result {r_1}). Sending measurement outcome to leaf {path[-1]} for correction.")
                    yield from self.send_msg_to_dist_node(context,path,str(r_1))
                    counter += 1
                    print(f"[Center {self.node_name}] Step {counter - 1} complete: Merged the second node. Currently forming a 3-node graph.")
            
                elif counter > 1:
                    print(f"[Center {self.node_name}] Step {counter}: Integrating another leaf {node} into the star graph.")
                    local_qubit = Qubit(context.connection)
                    local_qubit.H()
                    self.epr_qubit_1.H() 
                    local_qubit.cphase(self.epr_qubit_1)
                    self.center_qubit.cphase(local_qubit)
                    measurement1 = measXY(local_qubit,angle=np.pi/2)
                    measurement2 = measXY(self.epr_qubit_1,angle=np.pi/2)
                    
                    yield from context.connection.flush()
                    
                    counter += 1
                    print(f"---------[Center {self.node_name}] Step {counter - 1} complete: Successfully integrated leaf {node}. Star graph now includes {counter + 1} nodes.")
            
            else:
                try:
                    yield from 