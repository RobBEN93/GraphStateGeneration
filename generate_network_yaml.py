import yaml

def generate_linear_network_yaml(num_nodes, filename="/home/vor/VSCodeProjects/EntSwap/EntanglementSwapping/network_config.yaml"):
    
    node_names = [f"Node_{i}" for i in range(num_nodes)]

    # Default qdevice configuration (perfect case)
    qdevice_cfg = {
        'num_qubits': 2,
        # Coherence times (set to zero for perfect devices)
        'T1': 0,
        'T2': 0,
        # Gate execution times
        'init_time': 0,
        'single_qubit_gate_time': 0,
        'two_qubit_gate_time': 0,
        'measure_time': 0,
        # Noise model (set depolarization probabilities to zero)
        'single_qubit_gate_depolar_prob': 0.0,
        'two_qubit_gate_depolar_prob': 0.0,
    }

    # Default link configuration (perfect links)
    link_cfg = {
        'typ': 'perfect',
        'cfg': {
            'dummy': None  # Placeholder for any additional configuration
        }
    }

    # Default clink configuration (instant classical links)
    clink_cfg = {
        'typ': 'instant',
        'cfg': {
            'dummy': None  # Placeholder for any additional configuration
        }
    }

    # Generate stacks (nodes)
    stacks = []
    for name in node_names:
        stack = {
            'name': name,
            'qdevice_typ': 'generic',  # You can change this to 'nv' or other types
            'qdevice_cfg': qdevice_cfg
        }
        stacks.append(stack)

    # Generate links (quantum links between neighbors)
    links = []
    for i in range(num_nodes - 1):
        link = {
            'stack1': node_names[i],
            'stack2': node_names[i + 1],
            'typ': link_cfg['typ'],
            'cfg': link_cfg['cfg']
        }
        links.append(link)

    # Generate clinks (classical links between neighbors)
    clinks = []
    for i in range(num_nodes - 1):
        clink = {
            'stack1': node_names[i],
            'stack2': node_names[i + 1],
            'typ': clink_cfg['typ'],
            'cfg': clink_cfg['cfg']
        }
        clinks.append(clink)

    # Combine all configurations
    network_config = {
        'stacks': stacks,
        'links': links,
        'clinks': clinks
    }

    # Write to YAML file
    with open(filename, 'w') as f:
        yaml.dump(network_config, f, default_flow_style=False)

    print(f"Network configuration YAML file generated: {filename}")