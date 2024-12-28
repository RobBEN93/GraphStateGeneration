import yaml

def generate_yaml(num_nodes, links, use_noisy=False, include_link_cfg=False, include_clink_cfg=False):
    # Define the shared configurations for the nodes
    perfect_qdevice_cfg = {
        'perfect_qdevice_cfg': {
            'num_qubits': 4,
            'T1': 0,
            'T2': 0,
            'init_time': 0,
            'single_qubit_gate_time': 0,
            'two_qubit_gate_time': 0,
            'measure_time': 0,
            'single_qubit_gate_depolar_prob': 0.0,
            'two_qubit_gate_depolar_prob': 0.0,
        }
    }

    noisy_qdevice_cfg = {
        'noisy_qdevice_cfg': {
            'num_qubits': 4,
            'T1': 500_000_000,
            'T2': 500_000_000,
            'init_time': 10_000,
            'single_qubit_gate_time': 10_000,
            'two_qubit_gate_time': 10_000,
            'measure_time': 10_000,
            'single_qubit_gate_depolar_prob': 0.5,
            'two_qubit_gate_depolar_prob': 0.5,
        }
    }

    # Define the shared link configuration
    link_cfg = {
        'fidelity': 0.97,
        'prob_success': 0.2,
        'length': 10,
    }

    # Choose configuration
    chosen_cfg = noisy_qdevice_cfg if use_noisy else perfect_qdevice_cfg
    chosen_cfg_key = 'noisy_qdevice_cfg' if use_noisy else 'perfect_qdevice_cfg'

    # Define the stacks
    stacks = []
    for i in range(num_nodes):
        stacks.append({
            'name': f'node_{i}',
            'qdevice_typ': 'generic',
            'qdevice_cfg': {'<<': f'*{chosen_cfg_key}'}
        })

    # Define the quantum links
    link_entries = []
    for link in links:
        link_entry = {
            'stack1': f'node_{link[0]}',
            'stack2': f'node_{link[1]}',
            'typ': 'depolarise' if include_link_cfg else 'perfect',
        }
        if include_link_cfg:
            link_entry['cfg'] = {'<<': '*link_cfg'}
        link_entries.append(link_entry)

    # Define the classical links
    clink_entries = []
    for link in links:
        clink_entry = {
            'stack1': f'node_{link[0]}',
            'stack2': f'node_{link[1]}'
        }
        if include_clink_cfg:
            clink_entry['typ'] = 'default'
            clink_entry['cfg'] = {'length': 10}
        else:
            clink_entry['typ'] = 'instant'
        clink_entries.append(clink_entry)
    
    # Combine everything into the final structure
    if include_link_cfg:
        yaml_structure = {
            chosen_cfg_key: chosen_cfg[chosen_cfg_key],
            'stacks': stacks,
            'link_cfg' : link_cfg,
            'links': link_entries,
            'clinks': clink_entries
        }
    else:
        yaml_structure = {
            chosen_cfg_key: chosen_cfg[chosen_cfg_key],
            'stacks': stacks,
            'links': link_entries,
            'clinks': clink_entries
        }

   

    # Serialize to YAML
    yaml_output = yaml.dump(yaml_structure, sort_keys=False, default_flow_style=False)

    # Post-process replacements
    yaml_output = yaml_output.replace("'<<': '*perfect_qdevice_cfg'", "<<: *perfect_qdevice_cfg")
    yaml_output = yaml_output.replace("'<<': '*noisy_qdevice_cfg'", "<<: *noisy_qdevice_cfg")
    if include_link_cfg:
        yaml_output = yaml_output.replace("'<<': '*link_cfg'", "<<: *link_cfg")
        yaml_output = yaml_output.replace("link_cfg:", "link_cfg: &link_cfg")
    yaml_output = yaml_output.replace("perfect_qdevice_cfg:", "perfect_qdevice_cfg: &perfect_qdevice_cfg")
    yaml_output = yaml_output.replace("noisy_qdevice_cfg:", "noisy_qdevice_cfg: &noisy_qdevice_cfg")

    return yaml_output

num_nodes = 11
links = [
    (0, 1), (0, 2), (0, 6), (0, 8),
    (1, 2), (1, 3), (1, 4), (1, 9),
    (5, 8), (5, 7), (5, 10), (8, 10),
    (3, 7), (8, 9), (5, 4), (5, 1)
]

# Generate YAML with all configurations enabled
yaml_content_noisy = generate_yaml(num_nodes, links, use_noisy=True, include_link_cfg=True, include_clink_cfg=True)

# Generate YAML without link and clink configurations
yaml_content_ideal = generate_yaml(num_nodes, links, use_noisy=False, include_link_cfg=False, include_clink_cfg=False)

# Write to files
with open('network_configs/network_config_noisy.yaml', 'w') as file:
    file.write(yaml_content_noisy)

with open('network_configs/network_config_ideal.yaml', 'w') as file:
    file.write(yaml_content_ideal)

print("YAML files generated.")

num_nodes = 25
links = [
    (0, 1), (0, 2), (0, 14), (0, 23), (0, 24),
    (1, 2), (1, 3), (1, 19), (1, 24),
    (2, 3), (2, 4),
    (3, 4), (3, 5), (3, 19),
    (4, 5), (4, 6),
    (5, 7), (5, 23),
    (6, 7), (6, 8),
    (7, 9),
    (8, 9), (8, 10), (8, 23),
    (9, 10), (9, 11),
    (10, 11), (10, 12),
    (11, 12), (11, 13),
    (12, 13), (12, 14),
    (13, 14), (13, 15),
    (14, 16),
    (15, 16),
    (16, 17), (16, 18),
    (17, 18), (17, 19),
    (18, 19), (18, 20),
    (19, 20), (19, 21),
    (20, 21), (20, 22),
    (21, 22), (21, 23),
    (22, 23), (22, 24),
]

# Generate YAML with all configurations enabled
yaml_content_noisy = generate_yaml(num_nodes, links, use_noisy=True, include_link_cfg=True, include_clink_cfg=True)

# Generate YAML without link and clink configurations
yaml_content_ideal = generate_yaml(num_nodes, links, use_noisy=False, include_link_cfg=False, include_clink_cfg=False)

# Write to files
with open('network_configs/smallworld_config_noisy.yaml', 'w') as file:
    file.write(yaml_content_noisy)

with open('network_configs/smallworld_config_ideal.yaml', 'w') as file:
    file.write(yaml_content_ideal)

print("YAML files generated.")

num_nodes = 50
links = [
    # --- Ring edges (connect i to i+1, plus wrap-around) ---
    (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9),
    (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 16),
    (16, 17), (17, 18), (18, 19), (19, 20), (20, 21), (21, 22), (22, 23),
    (23, 24), (24, 25), (25, 26), (26, 27), (27, 28), (28, 29), (29, 30),
    (30, 31), (31, 32), (32, 33), (33, 34), (34, 35), (35, 36), (36, 37),
    (37, 38), (38, 39), (39, 40), (40, 41), (41, 42), (42, 43), (43, 44),
    (44, 45), (45, 46), (46, 47), (47, 48), (48, 49), (0, 49),

    # --- "Second-neighbor" edges (connect i to i+2, wrapping around) ---
    (0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7), (6, 8), (7, 9), (8, 10),
    (9, 11), (10, 12), (11, 13), (12, 14), (13, 15), (14, 16), (15, 17),
    (16, 18), (17, 19), (18, 20), (19, 21), (20, 22), (21, 23), (22, 24),
    (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), (28, 30), (29, 31),
    (30, 32), (31, 33), (32, 34), (33, 35), (34, 36), (35, 37), (36, 38),
    (37, 39), (38, 40), (39, 41), (40, 42), (41, 43), (42, 44), (43, 45),
    (44, 46), (45, 47), (46, 48), (47, 49), (0, 48), (1, 49),

    # --- Shortcut edges (random long-range connections) ---
    (0, 26), (0, 35),  (1, 22),  (2, 47),  (4, 25),  (5, 41),  (6, 42),
    (8, 23),  (9, 38),  (10, 35), (15, 24), (17, 36), (19, 39), (20, 45),
    (22, 34), (26, 44), (27, 49), (28, 47), (31, 45), (33, 48), (35, 49),
    (36, 47), (37, 45), (41, 48), (42, 49),
]

# Generate YAML with all configurations enabled
yaml_content_noisy = generate_yaml(num_nodes, links, use_noisy=True, include_link_cfg=True, include_clink_cfg=True)

# Generate YAML without link and clink configurations
yaml_content_ideal = generate_yaml(num_nodes, links, use_noisy=False, include_link_cfg=False, include_clink_cfg=False)

# Write to files
with open('network_configs/largesmallworld_config_noisy.yaml', 'w') as file:
    file.write(yaml_content_noisy)

with open('network_configs/largesmallworld_config_ideal.yaml', 'w') as file:
    file.write(yaml_content_ideal)

print("YAML files generated.")