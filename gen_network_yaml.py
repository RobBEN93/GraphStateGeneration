import yaml

def generate_yaml(num_nodes, links, use_noisy=False, include_link_cfg=False, include_clink_cfg=False):
    # Define the shared configurations for the nodes
    perfect_qdevice_cfg = {
        'perfect_qdevice_cfg': {
            'num_qubits': 2,
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
            'num_qubits': 2,
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

# Example usage
num_nodes = 11
links = [
    (0, 1), (0, 2), (0, 6), (0, 8),
    (1, 2), (1, 3), (1, 4), (1, 9)
]

# Generate YAML with all configurations enabled
yaml_content_noisy = generate_yaml(num_nodes, links, use_noisy=True, include_link_cfg=True, include_clink_cfg=True)

# Generate YAML without link and clink configurations
yaml_content_ideal = generate_yaml(num_nodes, links, use_noisy=False, include_link_cfg=False, include_clink_cfg=False)

# Write to files
with open('network_config_noisy.yaml', 'w') as file:
    file.write(yaml_content_noisy)

with open('network_config_ideal.yaml', 'w') as file:
    file.write(yaml_content_ideal)

print("YAML files generated successfully.")
