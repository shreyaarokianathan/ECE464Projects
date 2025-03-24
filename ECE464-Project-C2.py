import re

# Parse the .bench file to extract inputs, outputs, and gate connections
def parse_bench_file(file_path):
    inputs, outputs, gates = [], [], {}
    node_pattern = re.compile(r'\((.*?)\)')
    gate_pattern = re.compile(r'(.*?)\s*=\s*(.*?)\((.*?)\)')

    # Read and process each line of the file
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('INPUT'):
                inputs.append(node_pattern.search(line).group(1))  # Extract inputs
            elif line.startswith('OUTPUT'):
                outputs.append(node_pattern.search(line).group(1))  # Extract outputs
            elif '=' in line:
                match = gate_pattern.match(line)
                if match:
                    output, gate_type, inputs_str = match.groups()
                    gate_inputs = [inp.strip() for inp in inputs_str.split(',')]
                    gates[output.strip()] = {'type': gate_type, 'inputs': gate_inputs}  # Define gates

    return inputs, outputs, gates

# Evaluate logic gate based on its type and input values
def evaluate_gate(gate_type, input_values):
    if gate_type == 'AND':
        return int(all(input_values))
    elif gate_type == 'NAND':
        return int(not all(input_values))
    elif gate_type == 'OR':
        return int(any(input_values))
    elif gate_type == 'NOR':
        return int(not any(input_values))
    elif gate_type == 'XOR':
        return int(sum(input_values) % 2 == 1)
    elif gate_type == 'NOT':
        return int(not input_values[0])
    elif gate_type == 'BUFFER':
        return input_values[0]
    return input_values[0]  # Default behavior

# Simulate the circuit for given inputs and fault scenario (if any)
def simulate_circuit(inputs, outputs, gates, input_vector, fault=None):
    node_values = {node: input_vector[i] for i, node in enumerate(inputs)}  # Assign input values to nodes
    evaluated = set(inputs)

    # Evaluate gates one by one based on dependencies
    while len(evaluated) < len(inputs) + len(gates):
        for gate, info in gates.items():
            if gate not in evaluated and all(inp in evaluated for inp in info['inputs']):
                input_values = [node_values[inp] for inp in info['inputs']]

                # Apply stuck-at fault if present
                if fault and fault['type'] == 'sa' and gate == fault['node']:
                    node_values[gate] = fault['value']
                elif fault and fault['type'] == 'input_sa' and gate == fault['gate']:
                    input_index = info['inputs'].index(fault['input'])
                    input_values[input_index] = fault['value']
                    node_values[gate] = evaluate_gate(info['type'], input_values)
                else:
                    node_values[gate] = evaluate_gate(info['type'], input_values)

                evaluated.add(gate)  # Mark gate as evaluated

                print(f"Evaluating gate {gate} ({info['type']}): inputs = {input_values}, output = {node_values[gate]}")

    return {output: node_values[output] for output in outputs}  # Return final output values

# Parse fault from the fault string
def parse_fault(fault_str):
    if '-sa-' in fault_str:
        node, value = fault_str.split('-sa-')
        return {'type': 'sa', 'node': node, 'value': int(value)}
    elif '-' in fault_str:
        gate, input_node, value = fault_str.split('-')
        return {'type': 'input_sa', 'gate': gate, 'input': input_node, 'value': int(value)}
    else:
        raise ValueError("Invalid fault format")

# Simulate both normal and faulty circuits, then compare the results
def fault_simulation(file_path, test_vector, fault_str):
    inputs, outputs, gates = parse_bench_file(file_path)
    fault = parse_fault(fault_str)

    print("Normal circuit simulation:")
    normal_result = simulate_circuit(inputs, outputs, gates, test_vector)

    print("\nFaulty circuit simulation:")
    faulty_result = simulate_circuit(inputs, outputs, gates, test_vector, fault)

    print("\nComparison of results:")
    fault_detected = False
    for output in outputs:
        normal_value = normal_result[output]
        faulty_value = faulty_result[output]
        print(f"Output {output}: Normal = {normal_value}, Faulty = {faulty_value}")
        if normal_value != faulty_value:
            fault_detected = True

    # Conclusion based on the fault detection
    if fault_detected:
        print(f"\nConclusion: The test vector {test_vector} can detect the fault {fault_str}.")
    else:
        print(f"\nConclusion: The test vector {test_vector} cannot detect the fault {fault_str}.")

# Main function to run the simulation
def main():
    file_path = "c17.bench"

    with open(file_path, 'r') as f:
        input_count = sum(1 for line in f if line.strip().startswith('INPUT'))

    test_vector_str = input(f"Enter the test vector ({input_count} bits, comma-separated): ")
    test_vector = [int(bit) for bit in test_vector_str.split(',')]

    fault = input("Enter the fault (e.g., 10-sa-0 or 22-10-1): ")

    fault_simulation(file_path, test_vector, fault)

if __name__ == "__main__":
    main()

import re

def parse_bench_file(file_path):
    inputs, outputs, gates = [], [], {}
    node_pattern = re.compile(r'\((.*?)\)')
    gate_pattern = re.compile(r'(.*?)\s*=\s*(.*?)\((.*?)\)')

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('INPUT'):
                inputs.append(node_pattern.search(line).group(1))
            elif line.startswith('OUTPUT'):
                outputs.append(node_pattern.search(line).group(1))
            elif '=' in line:
                match = gate_pattern.match(line)
                if match:
                    output, gate_type, inputs_str = match.groups()
                    gate_inputs = [inp.strip() for inp in inputs_str.split(',')]
                    gates[output.strip()] = {'type': gate_type, 'inputs': gate_inputs}

    return inputs, outputs, gates

def evaluate_gate(gate_type, input_values):
    if gate_type == 'AND':
        return int(all(input_values))
    elif gate_type == 'NAND':
        return int(not all(input_values))
    elif gate_type == 'OR':
        return int(any(input_values))
    elif gate_type == 'NOR':
        return int(not any(input_values))
    elif gate_type == 'XOR':
        return int(sum(input_values) % 2 == 1)
    elif gate_type == 'NOT':
        return int(not input_values[0])
    elif gate_type == 'BUFFER':
        return input_values[0]
    return input_values[0]  # Default behavior

def simulate_circuit(inputs, outputs, gates, input_vector, fault=None):
    node_values = {node: input_vector[i] for i, node in enumerate(inputs)}

    # Apply input fault if present
    if fault and fault['type'] == 'sa' and fault['node'] in inputs:
        node_values[fault['node']] = fault['value']

    evaluated = set(inputs)
    while len(evaluated) < len(inputs) + len(gates):
        for gate, info in gates.items():
            if gate not in evaluated and all(inp in evaluated for inp in info['inputs']):
                input_values = [node_values[inp] for inp in info['inputs']]

                if fault and fault['type'] == 'sa' and gate == fault['node']:
                    node_values[gate] = fault['value']
                else:
                    node_values[gate] = evaluate_gate(info['type'], input_values)

                evaluated.add(gate)

                print(f"Evaluating gate {gate} ({info['type']}): inputs = {input_values}, output = {node_values[gate]}")

    return {output: node_values[output] for output in outputs}

def parse_fault(fault_str):
    if '-sa-' in fault_str:
        node, value = fault_str.split('-sa-')
        return {'type': 'sa', 'node': node, 'value': int(value)}
    else:
        raise ValueError("Invalid fault format. Use format: node-sa-value")

def fault_simulation(file_path, test_vector, fault_str):
    inputs, outputs, gates = parse_bench_file(file_path)
    fault = parse_fault(fault_str)

    print("Normal circuit simulation:")
    normal_result = simulate_circuit(inputs, outputs, gates, test_vector)

    print("\nFaulty circuit simulation:")
    faulty_result = simulate_circuit(inputs, outputs, gates, test_vector, fault)

    print("\nComparison of results:")
    fault_detected = False
    for output in outputs:
        normal_value = normal_result[output]
        faulty_value = faulty_result[output]
        print(f"Output {output}: Normal = {normal_value}, Faulty = {faulty_value}")
        if normal_value != faulty_value:
            fault_detected = True

    if fault_detected:
        print(f"\nConclusion: The test vector {test_vector} can detect the fault {fault_str}.")
    else:
        print(f"\nConclusion: The test vector {test_vector} cannot detect the fault {fault_str}.")

def main():
    file_path = "hw1.bench"

    with open(file_path, 'r') as f:
        input_count = sum(1 for line in f if line.strip().startswith('INPUT'))

    test_vector_str = input(f"Enter the test vector ({input_count} bits, comma-separated): ")
    test_vector = [int(bit) for bit in test_vector_str.split(',')]

    fault = input("Enter the fault (e.g., a-sa-0 for input 'a' stuck-at-0): ")

    fault_simulation(file_path, test_vector, fault)

if __name__ == "__main__":
    main()
