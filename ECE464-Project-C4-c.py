
import re

class Circuit:
    def __init__(self, file_path):
        self.inputs, self.outputs, self.gates = self.parse_bench_file(file_path)
        self.nodes = set(self.inputs + self.outputs + list(self.gates.keys()))
        self.fault_list = self.generate_full_fault_list()

    def parse_bench_file(self, file_path):
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

    def generate_full_fault_list(self):
        return [f"{node}-sa-{value}" for node in self.nodes for value in (0, 1)]

    @staticmethod
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
        return input_values[0]

    def simulate(self, input_vector, fault=None):
        node_values = dict(zip(self.inputs, input_vector))

        if fault:
            fault_node, fault_value = fault.split('-sa-')
            if fault_node in self.inputs:
                node_values[fault_node] = int(fault_value)

        evaluated = set(self.inputs)
        while len(evaluated) < len(self.nodes):
            for gate, info in self.gates.items():
                if gate not in evaluated and all(inp in evaluated for inp in info['inputs']):
                    input_values = [node_values[inp] for inp in info['inputs']]

                    if fault and gate == fault_node:
                        node_values[gate] = int(fault_value)
                    else:
                        node_values[gate] = self.evaluate_gate(info['type'], input_values)

                    evaluated.add(gate)

        return {output: node_values[output] for output in self.outputs}

def fault_simulation(circuit, test_vector):
    normal_result = circuit.simulate(test_vector)
    detected_faults = []
    undetected_faults = []

    for fault in circuit.fault_list:
        faulty_result = circuit.simulate(test_vector, fault)
        if any(normal_result[output] != faulty_result[output] for output in circuit.outputs):
            detected_faults.append(fault)
        else:
            undetected_faults.append(fault)

    return detected_faults, undetected_faults

def main():
    file_path = "c880.bench"
    circuit = Circuit(file_path)

    print(f"Circuit loaded. Inputs: {len(circuit.inputs)}, Outputs: {len(circuit.outputs)}, Gates: {len(circuit.gates)}")
    print(f"Total faults: {len(circuit.fault_list)}")

    print(f"Please enter a test vector of {len(circuit.inputs)} bits (0s and 1s):")
    user_input = input().strip()
    test_vector = [int(bit) for bit in user_input if bit in '01']

    if len(test_vector) != len(circuit.inputs):
        print(f"Error: Input vector must be {len(circuit.inputs)} bits long.")
        return

    detected_faults, undetected_faults = fault_simulation(circuit, test_vector)

    print("\nFault Simulation Results:")
    print("Detected faults:")
    for fault in detected_faults:
        print(fault)

    print("\nUndetected faults:")
    for fault in undetected_faults:
        print(fault)

    total_faults = len(circuit.fault_list)
    detected_count = len(detected_faults)
    coverage_percentage = (detected_count / total_faults) * 100

    print(f"\nTotal faults: {total_faults}")
    print(f"Total faults detected: {detected_count}")
    print(f"Fault coverage: {coverage_percentage:.2f}%")

if __name__ == "__main__":
    main()
