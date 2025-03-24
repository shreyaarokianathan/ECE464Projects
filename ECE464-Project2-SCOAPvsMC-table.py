import random
import re
from tabulate import tabulate

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



# Modified function to compare SCOAP and MC for each node
def compare_scoap_mc(nodes, scoap_results, mc_results, output_nodes):
    comparison_data = []

    for node_name, node in nodes.items():
        scoap_c0 = scoap_results[node_name].c0
        scoap_c1 = scoap_results[node_name].c1
        mc_c0_prob = mc_results[node_name][0]
        mc_c1_prob = mc_results[node_name][1]

        # Determine if there's a discrepancy
        c0_discrepancy = (scoap_c0 > scoap_c1 and mc_c0_prob > 0.5) or (scoap_c0 < scoap_c1 and mc_c0_prob < 0.5)
        c1_discrepancy = (scoap_c1 > scoap_c0 and mc_c1_prob > 0.5) or (scoap_c1 < scoap_c0 and mc_c1_prob < 0.5)

        # Categorize node
        category = "Input" if node.gate_type is None else ("Output" if node_name in output_nodes else "Intermediary")

        comparison_data.append({
            "Node": node_name,
            "SCOAP C0": scoap_c0,
            "SCOAP C1": scoap_c1,
            "MC C0 Prob": mc_c0_prob,
            "MC C1 Prob": mc_c1_prob,
            "C0 Discrepancy": "Yes" if c0_discrepancy else "No",
            "C1 Discrepancy": "Yes" if c1_discrepancy else "No",
            "Category": category
        })

    return comparison_data

# Modified function to print the comparative analysis table
def print_comparative_analysis_table(comparison_data):
    headers = ["Node", "SCOAP C0", "SCOAP C1", "MC C0 Prob", "MC C1 Prob", "C0 Discrepancy", "C1 Discrepancy", "Category"]
    table = [
        [
            entry['Node'],
            entry['SCOAP C0'],
            entry['SCOAP C1'],
            f"{entry['MC C0 Prob']:.2f}",
            f"{entry['MC C1 Prob']:.2f}",
            entry['C0 Discrepancy'],
            entry['C1 Discrepancy'],
            entry['Category']
        ]
        for entry in comparison_data
    ]
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

# Modified main function
def main():
    # Parse .bench file
    file_path = "c432.bench"  # Update with actual file path
    nodes, inputs, outputs, gates = parse_bench_file(file_path)

    # Compute SCOAP results
    scoap_results = compute_scoap(nodes)

    # Run Monte Carlo simulation
    mc_results = monte_carlo_simulation(nodes)

    # Compare SCOAP and Monte Carlo simulation results
    comparison_data = compare_scoap_mc(nodes, scoap_results, mc_results, outputs)

    # Print the results in tabular format
    print_comparative_analysis_table(comparison_data)

    # Calculate and print the percentage of nodes with discrepancies
    total_nodes = len(comparison_data)
    c0_discrepancies = sum(1 for entry in comparison_data if entry['C0 Discrepancy'] == "Yes")
    c1_discrepancies = sum(1 for entry in comparison_data if entry['C1 Discrepancy'] == "Yes")

    print(f"\nPercentage of nodes with C0 discrepancies: {(c0_discrepancies / total_nodes) * 100:.2f}%")
    print(f"Percentage of nodes with C1 discrepancies: {(c1_discrepancies / total_nodes) * 100:.2f}%")

if __name__ == "__main__":
    main()
