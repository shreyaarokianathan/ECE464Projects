import re
import random
import time

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
        fault_list = []
        for node in self.nodes:
            fault_list.append(f"{node}-sa-0")
            fault_list.append(f"{node}-sa-1")
        return fault_list

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

def fault_simulation(circuit, test_vectors):
    normal_results = [circuit.simulate(tv) for tv in test_vectors]
    detected_faults = set()

    for fault in circuit.fault_list:
        for i, tv in enumerate(test_vectors):
            faulty_result = circuit.simulate(tv, fault)
            if any(normal_results[i][output] != faulty_result[output] for output in circuit.outputs):
                detected_faults.add(fault)
                break

    return list(detected_faults), [f for f in circuit.fault_list if f not in detected_faults]

def generate_random_test_vector(input_count):
    return [random.randint(0, 1) for _ in range(input_count)]

def incremental_fault_simulation(circuit, initial_vector_count=10, increment=10, max_vectors=200):
    results = []
    all_detected_faults = set()
    test_vectors = []

    for i in range(0, max_vectors, increment):
        new_vectors = [generate_random_test_vector(len(circuit.inputs)) for _ in range(increment)]
        test_vectors.extend(new_vectors)

        detected_faults, _ = fault_simulation(circuit, test_vectors)
        new_faults = set(detected_faults) - all_detected_faults
        all_detected_faults.update(new_faults)

        fault_coverage = len(all_detected_faults) / len(circuit.fault_list) * 100

        results.append({
            'vector_count': len(test_vectors),
            'fault_coverage': fault_coverage,
            'new_faults': len(new_faults)
        })

    return results

def main():
    circuits = ['c1908.bench']

    for circuit_file in circuits:
        print(f"Analyzing {circuit_file}")
        start_time = time.time()

        circuit = Circuit(circuit_file)
        results = incremental_fault_simulation(circuit)

        end_time = time.time()
        execution_time = end_time - start_time

        print("\nResults:")
        print("Vector Count | Fault Coverage (%) | New Faults Detected")
        print("-" * 50)
        for r in results:
            print(f"{r['vector_count']:12d} | {r['fault_coverage']:18.2f} | {r['new_faults']:20d}")

        print(f"\nExecution time: {execution_time:.2f} seconds")
        print("\n")

if __name__ == "__main__":
    main()