import re

def parse_bench_file(file_path):
    """
    Parse the .bench file to extract circuit inputs, outputs, and gate configurations.

    Arguments:
    file_path -- Path to the .bench file

    Returns:
    inputs -- List of input nodes
    outputs -- List of output nodes
    gates -- Dictionary mapping gate outputs to their types and input nodes
    """
    inputs, outputs, gates = [], [], {}
    node_pattern = re.compile(r'\((.*?)\)')  # Regex to extract node names within parentheses
    gate_pattern = re.compile(r'(.*?)\s*=\s*(.*?)\((.*?)\)')  # Regex to capture gate expressions

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('INPUT'):  # Identify and store input nodes
                inputs.append(node_pattern.search(line).group(1))
            elif line.startswith('OUTPUT'):  # Identify and store output nodes
                outputs.append(node_pattern.search(line).group(1))
            elif '=' in line:  # Parse gate expressions
                match = gate_pattern.match(line)
                if match:
                    output, gate_type, inputs_str = match.groups()
                    gate_inputs = [inp.strip() for inp in inputs_str.split(',')]  # Split gate inputs
                    gates[output.strip()] = {'type': gate_type, 'inputs': gate_inputs}

    return inputs, outputs, gates

def simulate_circuit(inputs, outputs, gates, input_vector):
    """
    Simulate the circuit's behavior based on a given input vector.

    Arguments:
    inputs -- List of input nodes
    outputs -- List of output nodes
    gates -- Dictionary containing gate configurations
    input_vector -- List of binary values representing the input vector

    Returns:
    Dictionary mapping output nodes to their computed binary values
    """
    # Initialize node values with input vector
    node_values = {node: input_vector[i] for i, node in enumerate(inputs)}

    def evaluate_gate(gate_type, input_values):
        """
        Evaluate the logical operation for a given gate based on its type and input values.

        Arguments:
        gate_type -- String representing the gate's operation (e.g., AND, OR, NOT)
        input_values -- List of boolean values representing gate input values

        Returns:
        Boolean result of the gate's evaluation
        """
        if gate_type == 'AND':
            return all(input_values)
        elif gate_type == 'NAND':
            return not all(input_values)
        elif gate_type == 'OR':
            return any(input_values)
        elif gate_type == 'NOR':
            return not any(input_values)
        elif gate_type == 'XOR':
            return sum(input_values) % 2 == 1
        elif gate_type == 'NOT':
            return not input_values[0]
        elif gate_type == 'BUFFER':
            return input_values[0]
        else:
            # Default to buffer behavior for unknown gate types
            return input_values[0]

    # Topological evaluation of the circuit (sequentially evaluate gates after inputs)
    evaluated = set(inputs)
    while len(evaluated) < len(inputs) + len(gates):  # Continue until all gates are evaluated
        for gate, info in gates.items():
            if gate not in evaluated and all(inp in evaluated for inp in info['inputs']):
                input_values = [node_values[inp] for inp in info['inputs']]  # Gather input values for the gate
                node_values[gate] = evaluate_gate(info['type'], input_values)  # Evaluate gate
                evaluated.add(gate)  # Mark gate as evaluated

    return {output: node_values[output] for output in outputs}  # Return the final output values

def main():
    """
    Main function to simulate the circuit described in a .bench file.
    Simulates the circuit for both all-0 and all-1 input vectors.
    """
    file_path = "c880.bench"  # Specify the path to the .bench file
    inputs, outputs, gates = parse_bench_file(file_path)

    # Simulate the circuit for all-0 input vector
    all_zero_input = [0] * len(inputs)  # Input vector with all-0 values
    all_zero_result = simulate_circuit(inputs, outputs, gates, all_zero_input)
    print("Simulation results for all-0 input vector:")
    for output, value in all_zero_result.items():
        print(f"{output}: {int(value)}")  # Convert boolean to integer for readability

    print("\n")

    # Simulate the circuit for all-1 input vector
    all_one_input = [1] * len(inputs)  # Input vector with all-1 values
    all_one_result = simulate_circuit(inputs, outputs, gates, all_one_input)
    print("Simulation results for all-1 input vector:")
    for output, value in all_one_result.items():
        print(f"{output}: {int(value)}")  # Convert boolean to integer for readability

if __name__ == "__main__":
    main()
