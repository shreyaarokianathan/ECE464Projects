import re
from collections import defaultdict

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
                    gates[output] = {'type': gate_type, 'inputs': gate_inputs}

    return inputs, outputs, gates

def generate_fault_list(inputs, outputs, gates):
    fault_list = defaultdict(list)

    for node in inputs + outputs + list(gates.keys()):
        fault_list[node].extend([f"{node}-sa-0", f"{node}-sa-1"])

    for gate, info in gates.items():
        for input_node in info['inputs']:
            fault_list[gate].extend([f"{gate}.{input_node}-sa-0", f"{gate}.{input_node}-sa-1"])

    return fault_list

def print_fault_list(fault_list, inputs, outputs, gates):
    def print_section(title, nodes, is_gate=False):
        print(f"\n{title}")
        print("-" * len(title))
        for node in sorted(nodes):
            faults = fault_list[node]
            if is_gate:
                output_faults = [f for f in faults if '.' not in f]
                input_faults = [f for f in faults if '.' in f]
                print(f"  {node}:")
                print(f"    Output: {', '.join(output_faults)}")
                print(f"    Inputs: {', '.join(input_faults)}")
            else:
                print(f"  {node}: {', '.join(faults)}")

    print_section("Input Faults", inputs)
    print_section("Internal Node Faults", [g for g in gates if g not in outputs], True)
    print_section("Output Faults", outputs, True)

    total_faults = sum(len(faults) for faults in fault_list.values())
    print(f"\nTotal number of faults: {total_faults}")

    # Print statistics
    print("\nCircuit Statistics:")
    print(f"  Number of inputs: {len(inputs)}")
    print(f"  Number of outputs: {len(outputs)}")
    print(f"  Number of gates: {len(gates)}")
    gate_types = defaultdict(int)
    for gate in gates.values():
        gate_types[gate['type']] += 1
    print("  Gate types:")
    for gate_type, count in gate_types.items():
        print(f"    {gate_type}: {count}")

def main():
    file_path = "c432.bench"  
    inputs, outputs, gates = parse_bench_file(file_path)
    fault_list = generate_fault_list(inputs, outputs, gates)
    print_fault_list(fault_list, inputs, outputs, gates)

if __name__ == "__main__":
    main()
