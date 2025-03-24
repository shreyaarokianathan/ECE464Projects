import random
import re

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

def evaluate_circuit(nodes, input_values):
    # Set the input values and update c0, c1 for input nodes
    for input_node in nodes.values():
        if input_node.gate_type is None:  # Input node
            input_node.value = input_values[input_node.name]
            # Controllability should not be updated directly, only through gate propagation
            # Update controllability values for inputs based on gate outcomes
            if input_node.value == 0:
                input_node.c0 += 1
            else:
                input_node.c1 += 1

    # Propagate the values through the gates
    for node in nodes.values():
        if node.gate_type is None:  # Skip input nodes
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
            node.value = 1 - input_values[0]  # Invert the input value
        elif node.gate_type == "BUFFER":
            node.value = input_values[0]  # Pass the value through

    return nodes


def monte_carlo_simulation(nodes, num_simulations=1000):
    # Initialize counts for each node
    node_counts = {node.name: {0: 0, 1: 0} for node in nodes.values()}
    input_counts = {node.name: {0: 0, 1: 0} for node in nodes.values() if node.gate_type is None}
    simulation_results = []

    # Run the Monte Carlo simulation
    for i in range(num_simulations):
        # Generate a random input pattern (0 or 1 for each input node)
        input_values = {input_node.name: random.choice([0, 1]) for input_node in nodes.values() if input_node.gate_type is None}

        # Evaluate the circuit for the current input pattern
        evaluate_circuit(nodes, input_values)

        # Store the results for each node and the input values
        result = {'serial_no': i + 1, 'input_values': input_values.copy(), 'node_results': {}}
        for node in nodes.values():
            if node.gate_type is not None and node.value is not None:  # Skip input nodes and nodes without values
                result['node_results'][node.name] = node.value
                node_counts[node.name][node.value] += 1
            if node.gate_type is None:  # Count for input nodes
                input_counts[node.name][input_values[node.name]] += 1

        simulation_results.append(result)

    return node_counts, input_counts, simulation_results


# Function to print results with percentages for node results
def print_node_results(node_counts, num_simulations=1000):
    print(f"{'Node':<10} {'0 Count':<10} {'1 Count':<10} {'0 Percentage':<15} {'1 Percentage':<15}")
    print("-" * 50)
    for node, counts in node_counts.items():
        count_0 = counts[0]
        count_1 = counts[1]
        perc_0 = (count_0 / num_simulations) * 100
        perc_1 = (count_1 / num_simulations) * 100
        print(f"{node:<10} {count_0:<10} {count_1:<10} {perc_0:<15.2f} {perc_1:<15.2f}")

# Function to print results for input values
def print_input_results(input_counts, num_simulations=1000):
    print(f"{'Node':<10} {'0 Count':<10} {'1 Count':<10} {'0 Percentage':<15} {'1 Percentage':<15}")
    print("-" * 50)
    for node, counts in input_counts.items():
        count_0 = counts[0]
        count_1 = counts[1]
        perc_0 = (count_0 / num_simulations) * 100
        perc_1 = (count_1 / num_simulations) * 100
        print(f"{node:<10} {count_0:<10} {count_1:<10} {perc_0:<15.2f} {perc_1:<15.2f}")

# Function to print the simulation result table
def print_simulation_table(simulation_results):
    print(f"{'SNo.':<12} {'Input Values':<30} {'Node Results':<30}")
    print("-" * 72)
    for result in simulation_results:
        input_str = ', '.join([f"{key}={value}" for key, value in result['input_values'].items()])
        node_str = ', '.join([f"{key}={value}" for key, value in result['node_results'].items()])
        print(f"{result['serial_no']:<12} {input_str:<30} {node_str:<30}")


def print_separated_tables(node_counts, input_counts, outputs, simulation_results, num_simulations=10):

    # Print Simulation Summary
    print("\nSimulation Results Summary:")
    print_simulation_table(simulation_results)

    # Print Inputs
    print("\nInput Nodes Results:")
    print_input_results(input_counts, num_simulations)

    # Print Intermediate Nodes
    print("\nIntermediate Nodes Results:")
    intermediate_counts = {node: node_counts[node] for node in node_counts if node not in input_counts and node not in outputs}
    print_node_results(intermediate_counts, num_simulations)

    # Print Outputs
    print("\nOutput Nodes Results:")
    output_counts = {node: node_counts[node] for node in node_counts if node in outputs}
    print_node_results(output_counts, num_simulations)




def main(file_path, num_simulations=1000):
    nodes, inputs, outputs, gates = parse_bench_file(file_path)
    nodes = compute_scoap(nodes)
    node_counts, input_counts, simulation_results = monte_carlo_simulation(nodes, num_simulations)
    print_separated_tables(node_counts, input_counts, outputs, simulation_results, num_simulations)

# file path
file_path = "p2.bench"
main(file_path)

