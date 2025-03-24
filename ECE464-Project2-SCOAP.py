import re

# Node class to represent each component in the circuit
class Node:
    def __init__(self, name):
        self.name = name
        self.c0 = 0  # Controllability 0
        self.c1 = 0  # Controllability 1
        self.inputs = []
        self.gate_type = None

    def __repr__(self):
        return f"{self.name}: C0 = {self.c0}, C1 = {self.c1}"


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


# Function to print SCOAP results
def print_scoap_results(nodes):
    print(f"{'Node':<10} {'C0':<10} {'C1':<10}")
    print("-" * 30)
    for node in nodes.values():
        print(f"{node.name:<10} {node.c0:<10} {node.c1:<10}")


if __name__ == "__main__":
    # Bench file path
    bench_file = "p2.bench"

    # Parse the bench file
    nodes, inputs, outputs, gates = parse_bench_file(bench_file)

    # Compute SCOAP metrics
    compute_scoap(nodes)

    # Print results
    print_scoap_results(nodes)
