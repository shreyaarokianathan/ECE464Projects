import re

class Circuit:
    def __init__(self, file_path):
        # Initialize circuit by parsing the bench file for inputs, outputs, and gates
        self.inputs, self.outputs, self.gates = self.parse_bench_file(file_path)
        # Create a set of all nodes (inputs, outputs, and gates)
        self.nodes = set(self.inputs + self.outputs + list(self.gates.keys()))
        # Generate a list of possible faults for each node
        self.fault_list = self.generate_full_fault_list()

    def parse_bench_file(self, file_path):
        inputs, outputs, gates = [], [], {}
        node_pattern = re.compile(r'\((.*?)\)')  # Pattern to match node names
        gate_pattern = re.compile(r'(.*?)\s*=\s*(.*?)\((.*?)\)')  # Pattern for gate definitions

        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()  # Remove whitespace
                if line.startswith('INPUT'):
                    inputs.append(node_pattern.search(line).group(1))  # Add input node
                elif line.startswith('OUTPUT'):
                    outputs.append(node_pattern.search(line).group(1))  # Add output node
                elif '=' in line:
                    match = gate_pattern.match(line)  # Match gate definition
                    if match:
                        output, gate_type, inputs_str = match.groups()
                        gate_inputs = [inp.strip() for inp in inputs_str.split(',')]  # Parse gate inputs
                        gates[output.strip()] = {'type': gate_type, 'inputs': gate_inputs}  # Store gate info

        return inputs, outputs, gates

    def generate_full_fault_list(self):
        # Create fault list for each node with stuck-at faults
        return [f"{node}-sa-{value}" for node in self.nodes for value in (0, 1)]

    @staticmethod
    def evaluate_gate(gate_type, input_values):
        # Evaluate gate output based on its type and input values
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

    def simulate(self, input_vector, fault=None):
        # Initialize node values from input vector
        node_values = dict(zip(self.inputs, input_vector))

        # Apply fault if specified
        if fault:
            fault_node, fault_value = fault.split('-sa-')
            if fault_node in self.inputs:
                node_values[fault_node] = int(fault_value)

        evaluated = set(self.inputs)  # Set of evaluated nodes
        while len(evaluated) < len(self.nodes):  # Process until all nodes are evaluated
            for gate, info in self.gates.items():
                if gate not in evaluated and all(inp in evaluated for inp in info['inputs']):
                    input_values = [node_values[inp] for inp in info['inputs']]  # Get input values

                    # Evaluate the gate with or without the fault
                    if fault and gate == fault_node:
                        node_values[gate] = int(fault_value)  # Apply fault
                    else:
                        node_values[gate] = self.evaluate_gate(info['type'], input_values)  # Normal evaluation

                    evaluated.add(gate)  # Mark gate as evaluated

        return {output: node_values[output] for output in self.outputs}  # Return output values

def fault_simulation(circuit, test_vector):
    # Simulate circuit behavior for a given test vector
    normal_result = circuit.simulate(test_vector)  # Get normal output
    detected_faults = []  # List for detected faults
    undetected_faults = []  # List for undetected faults

    for fault in circuit.fault_list:
        faulty_result = circuit.simulate(test_vector, fault)  # Simulate with fault
        # Compare normal and faulty results
        if any(normal_result[output] != faulty_result[output] for output in circuit.outputs):
            detected_faults.append(fault)  # Fault detected
        else:
            undetected_faults.append(fault)  # Fault not detected

    return detected_faults, undetected_faults  # Return detected and undetected faults

def main():
    file_path = "c880.bench"  # Specify the bench file path
    circuit = Circuit(file_path)  # Load circuit from file

    print(f"Circuit loaded. Inputs: {len(circuit.inputs)}, Outputs: {len(circuit.outputs)}, Gates: {len(circuit.gates)}")
    print(f"Total faults: {len(circuit.fault_list)}")

    # Generate all-zero input vector
    test_vector = [0] * len(circuit.inputs)
    print(f"Using all-zero test vector: {test_vector}")

    detected_faults, undetected_faults = fault_simulation(circuit, test_vector)  # Run fault simulation

    print("\nFault Simulation Results:")
    print("Detected faults:")
    for fault in detected_faults:
        print(fault)  # Print detected faults

    print("\nUndetected faults:")
    for fault in undetected_faults:
        print(fault)  # Print undetected faults

    total_faults = len(circuit.fault_list)  # Count total faults
    detected_count = len(detected_faults)  # Count detected faults
    coverage_percentage = (detected_count / total_faults) * 100  # Calculate fault coverage

    print(f"\nTotal faults detected: {detected_count}")
    print(f"Fault coverage: {coverage_percentage:.2f}%")

if __name__ == "__main__":
    main()  # Execute the main function
