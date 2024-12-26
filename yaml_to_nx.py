import yaml
import networkx as nx
import matplotlib.pyplot as plt

def yaml_to_nx(filename, detailed=False, weighted=False):
    """
    Build a NetworkX graph from a YAML file.
    
    Parameters
    ----------
    filename : str
        Path to the YAML configuration file.
    detailed : bool, optional
        If False, create a simple graph with only node and edge identifiers.
        If True, include attributes from the YAML such as qdevice_cfg, link cfg, etc.
    weighted : bool, optional
        If True, assign a 'weight' attribute to edges based solely on YAML data.
        In this example, 'weight' is taken from cfg['length'] if available.

    Returns
    -------
    nx.Graph
        The constructed graph.
    """
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)
    
    G = nx.Graph()

    # Add nodes from stacks
    for stack in data.get('stacks', []):
        node_name = stack['name']
        if detailed:
            # Include qdevice config and potentially other info directly from YAML
            node_attrs = {
                key: val for key, val in stack.items() if key not in ['name']
            }
        else:
            # Only store node name, no additional info
            node_attrs = {}
        
        G.add_node(node_name, **node_attrs)

    def add_edges_from_config(edges, edge_type='link'):
        for e in edges:
            stack1 = e['stack1']
            stack2 = e['stack2']
            
            if detailed:
                # Include all YAML-provided attributes (typ, cfg, etc.)
                edge_attrs = {
                    key: val for key, val in e.items() if key not in ['stack1', 'stack2']
                }
                edge_attrs['edge_type'] = edge_type
            else:
                # Only record that this edge exists, no extra attributes
                edge_attrs = {}

            # If weighted, try to assign weight from YAML info
            if weighted and detailed:
                cfg = e.get('cfg', {})
                # Use 'length' if available for weight
                if 'length' in cfg:
                    edge_attrs['weight'] = cfg['length']

            G.add_edge(stack1, stack2, **edge_attrs)

    # Add quantum links (links) and classical links (clinks)
    add_edges_from_config(data.get('links', []), edge_type='quantum_link')
    add_edges_from_config(data.get('clinks', []), edge_type='classical_link')

    return G

def visualize_graph(G, show_node_labels=True, show_edge_labels=False, layout='spring', node_color='lightblue'):
    """
    Visualize a NetworkX graph using matplotlib.

    Parameters
    ----------
    G : networkx.Graph
        The graph to visualize.
    show_node_labels : bool, optional
        If True, node labels from G nodes will be displayed.
    show_edge_labels : bool, optional
        If True, edge labels (if any) will be displayed.
    layout : str, optional
        The layout method to use for positioning the nodes. 
        Options: 'spring', 'circular', 'shell', 'random', 'kamada_kawai'
    node_color : str or list, optional
        Matplotlib color string or list of colors for nodes.

    """
    # Select layout
    if layout == 'spring':
        pos = nx.spring_layout(G)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'shell':
        pos = nx.shell_layout(G)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.random_layout(G)

    # Draw the graph
    nx.draw(G, pos, with_labels=False, node_color=node_color, edge_color='gray', node_size=500, font_size=10)

    if show_node_labels:
        # Draw node labels (just the node names by default)
        labels = {n: n for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=10)

    if show_edge_labels:
        # If the graph has attributes for edges, you might select one attribute to display.
        # By default, let's show the 'weight' if it exists, or 'typ' if no weight.
        if all('weight' in data for _,_,data in G.edges(data=True)):
            edge_labels = {(u,v): f"{data.get('weight')}" for u,v,data in G.edges(data=True)}
        else:
            # Fall back to showing 'typ' if weight isn't present
            edge_labels = {(u,v): f"{data.get('typ', '')}" for u,v,data in G.edges(data=True)}
        
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, rotate=False)

    plt.axis('off')
    plt.show()
   
def shortest_path(G,end_nodes):
    path = nx.dijkstra_path(G,source=end_nodes[0], target=end_nodes[1])
    return path