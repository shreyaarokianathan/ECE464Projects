import random
import re
import matplotlib.pyplot as plt
import pandas as pd

# Node class to represent each component in the circuit
class Node:
    def __init__(self, name):
        self.name = name
        self.c0 = 0  # Controllability 0
        self.c1 = 0  # Controllability 1
        self.inputs = []
        self.gate_type = None
        self.value = None  # Value after evaluation

    def __repr__(self):
        return f"{self.name}: C0 = {self.c0}, C1 = {self.c1}, Value = {self.value}"


# Function to parse the bench file
def parse_bench_file(file_path):
    nodes = {}
    inputs = []
    outputs = []
    gates = []

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Match INPUT, OUTPUT
            if line.startswith("INPUT("):
                input_name = re.search(r"INPUT\((\w+)\)", line).group(1)
                node = Node(input_name)
                node.c0, node.c1 = 1, 1  # Inputs default to C0=1, C1=1
                nodes[input_name] = node
                inputs.append(node)

            elif line.startswith("OUTPUT("):
                output_name = re.search(r"OUTPUT\((\w+)\)", line).group(1)
                outputs.append(output_name)

            # Match gates
            else:
                gate_match = re.match(r"(\w+)\s*=\s*(\w+)\(([\w,\s]+)\)", line)
                if gate_match:
                    node_name, gate_type, gate_inputs = gate_match.groups()
                    gate_inputs = gate_inputs.replace(" ", "").split(",")
                    node = Node(node_name)
                    node.gate_type = gate_type.upper()
                    node.inputs = gate_inputs
                    nodes[node_name] = node
                    gates.append(node)

    return nodes, inputs, outputs, gates


# Function to compute SCOAP metrics
def compute_scoap(nodes):
    def get_node(name):
        return nodes[name]

    for node in nodes.values():
        if node.gate_type is None:  # Skip inputs
            continue

        input_nodes = [get_node(inp) for inp in node.inputs]

        if node.gate_type == "AND":
            node.c0 = min(inp.c0 for inp in input_nodes) + 1
            node.c1 = sum(inp.c1 for inp in input_nodes) + 1

        elif node.gate_type == "OR":
            node.c0 = sum(inp.c0 for inp in input_nodes) + 1
            node.c1 = min(inp.c1 for inp in input_nodes) + 1

        elif node.gate_type == "NAND":
            node.c0 = sum(inp.c1 for inp in input_nodes) + 1
            node.c1 = min(inp.c0 for inp in input_nodes) + 1

        elif node.gate_type == "NOR":
            node.c0 = min(inp.c1 for inp in input_nodes) + 1
            node.c1 = sum(inp.c0 for inp in input_nodes) + 1

        elif node.gate_type == "NOT":
            node.c0 = input_nodes[0].c1 + 1
            node.c1 = input_nodes[0].c0 + 1

        elif node.gate_type == "BUFFER":
            node.c0 = input_nodes[0].c0
            node.c1 = input_nodes[0].c1

    return nodes


# Function to evaluate circuit for Monte Carlo simulation
def evaluate_circuit(nodes, input_values):
    for input_node in nodes.values():
        if input_node.gate_type is None:  # Input node
            input_node.value = input_values[input_node.name]

    for node in nodes.values():
        if node.gate_type is None:
            continue

        input_values = [nodes[input_name].value for input_name in node.inputs]
        if node.gate_type == "AND":
            node.value = 1 if all(input_values) else 0
        elif node.gate_type == "OR":
            node.value = 1 if any(input_values) else 0
        elif node.gate_type == "NAND":
            node.value = 0 if all(input_values) else 1
        elif node.gate_type == "NOR":
            node.value = 0 if any(input_values) else 1
        elif node.gate_type == "NOT":
            node.value = 1 - input_values[0]
        elif node.gate_type == "BUFFER":
            node.value = input_values[0]

    return nodes


# Function for Monte Carlo simulation (using probabilities)
def monte_carlo_simulation(nodes, num_simulations=1000):
    node_probs = {node.name: {0: 0, 1: 0} for node in nodes.values()}

    for _ in range(num_simulations):
        input_values = {node.name: random.choice([0, 1]) for node in nodes.values() if node.gate_type is None}
        evaluate_circuit(nodes, input_values)

        for node in nodes.values():
            if node.value is not None:
                node_probs[node.name][node.value] += 1

    # Convert counts to probabilities
    for node in node_probs:
        node_probs[node][0] /= num_simulations
        node_probs[node][1] /= num_simulations

    return node_probs


# Function to normalize SCOAP values to percentages
def normalize_scoap_to_percentages(nodes):
    for node in nodes.values():
        if node.c0 + node.c1 > 0:
            node.c0_percent = (node.c0 / (node.c0 + node.c1)) * 100
            node.c1_percent = (node.c1 / (node.c0 + node.c1)) * 100
        else:
            node.c0_percent = 0
            node.c1_percent = 0
    return nodes



# Function to categorize nodes
def categorize_nodes(nodes):
    input_nodes = []
    intermediary_nodes = []
    output_nodes = []

    for node in nodes.values():
        if node.gate_type is None:  # Input node
            input_nodes.append(node)
        elif node.gate_type:  # Gate node
            intermediary_nodes.append(node)
        if node.name in output_nodes:  # Output nodes
            output_nodes.append(node)

    return input_nodes, intermediary_nodes, output_nodes

# Function to visualize results for separated categories (Input, Intermediary, Output)
def visualize_comparison_separated(comparison_data, category):
    # Create a DataFrame for easy plotting
    df = pd.DataFrame(comparison_data)

    # Filter the data for the given category
    df_filtered = df[df['Category'] == category]

    # Plot a grouped stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot the data for C0 and C1
    df_filtered.set_index('Node')[['SCOAP C0 (%)', 'MC C0 Prob (%)']].plot(kind='bar', stacked=True, ax=ax, position=1, width=0.4, color=['blue', 'red'])
    df_filtered.set_index('Node')[['SCOAP C1 (%)', 'MC C1 Prob (%)']].plot(kind='bar', stacked=True, ax=ax, position=0, width=0.4, color=['lightblue', 'salmon'])

    ax.set_ylabel("Values (%)")
    ax.set_title(f"SCOAP vs Monte Carlo - C0 and C1 Probabilities for {category} Nodes")
    ax.set_xlabel("Nodes")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend(["SCOAP C0", "MC C0", "SCOAP C1", "MC C1"], loc='best')
    plt.show()

# Function to compare SCOAP and MC for each node, categorizing as input, intermediary, output
def compare_scoap_mc_separated(nodes, scoap_results, mc_results):
    comparison_data = []
    for node_name, node in nodes.items():
        if node_name not in scoap_results:
            continue

        scoap_c0_percent = scoap_results[node_name].c0_percent
        scoap_c1_percent = scoap_results[node_name].c1_percent
        mc_c0_prob = mc_results[node_name][0] * 100
        mc_c1_prob = mc_results[node_name][1] * 100

        # Categorize node
        category = "Input" if node.gate_type is None else ("Output" if node_name in output_nodes else "Intermediary")

        comparison_data.append({
            "Node": node_name,
            "SCOAP C0 (%)": scoap_c0_percent,
            "SCOAP C1 (%)": scoap_c1_percent,
            "MC C0 Prob (%)": mc_c0_prob,
            "MC C1 Prob (%)": mc_c1_prob,
            "Category": category
        })

    return comparison_data


# Function for analysis
def analyze_results(comparison_data):
    input_nodes = [entry for entry in comparison_data if entry['Category'] == 'Input']
    intermediary_nodes = [entry for entry in comparison_data if entry['Category'] == 'Intermediary']
    output_nodes = [entry for entry in comparison_data if entry['Category'] == 'Output']

    def calculate_avg_error(nodes):
        scoap_c0 = sum(entry['SCOAP C0 (%)'] for entry in nodes) / len(nodes)
        scoap_c1 = sum(entry['SCOAP C1 (%)'] for entry in nodes) / len(nodes)
        mc_c0 = sum(entry['MC C0 Prob (%)'] for entry in nodes) / len(nodes)
        mc_c1 = sum(entry['MC C1 Prob (%)'] for entry in nodes) / len(nodes)

        # Calculate absolute percentage error
        c0_error = abs(scoap_c0 - mc_c0)
        c1_error = abs(scoap_c1 - mc_c1)

        return scoap_c0, scoap_c1, mc_c0, mc_c1, c0_error, c1_error

    # Compute for each category
    input_avg = calculate_avg_error(input_nodes)
    intermediary_avg = calculate_avg_error(intermediary_nodes)
    output_avg = calculate_avg_error(output_nodes)

    print("Category-wise average results and errors (SCOAP vs MC):")
    print(f"Input Nodes - SCOAP C0: {input_avg[0]:.2f}, SCOAP C1: {input_avg[1]:.2f}, MC C0: {input_avg[2]:.2f}, MC C1: {input_avg[3]:.2f}, C0 Error: {input_avg[4]:.2f}%, C1 Error: {input_avg[5]:.2f}%")
    print(f"Intermediary Nodes - SCOAP C0: {intermediary_avg[0]:.2f}, SCOAP C1: {intermediary_avg[1]:.2f}, MC C0: {intermediary_avg[2]:.2f}, MC C1: {intermediary_avg[3]:.2f}, C0 Error: {intermediary_avg[4]:.2f}%, C1 Error: {intermediary_avg[5]:.2f}%")
    print(f"Output Nodes - SCOAP C0: {output_avg[0]:.2f}, SCOAP C1: {output_avg[1]:.2f}, MC C0: {output_avg[2]:.2f}, MC C1: {output_avg[3]:.2f}, C0 Error: {output_avg[4]:.2f}%, C1 Error: {output_avg[5]:.2f}%")


# Main code
if __name__ == "__main__":
    file_path = "c432.bench"
    nodes, input_nodes, output_nodes, gates = parse_bench_file(file_path)

    # Compute SCOAP values
    scoap_results = compute_scoap(nodes)
    scoap_results = normalize_scoap_to_percentages(scoap_results)

    # Run Monte Carlo simulation
    mc_results = monte_carlo_simulation(nodes)

    # Compare SCOAP vs MC with categories
    comparison_data = compare_scoap_mc_separated(nodes, scoap_results, mc_results)

    # Visualize results separately for Input, Intermediary, and Output nodes
    for category in ["Input", "Intermediary", "Output"]:
        visualize_comparison_separated(comparison_data, category)

    # Analyze the results
    analyze_results(comparison_data)

