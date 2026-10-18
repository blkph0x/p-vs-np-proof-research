"""Tseitin CNF for the nonlinear Hamming-weight circuit control."""

from __future__ import annotations


def _validate_forms(forms, dimension):
    forms = tuple(forms)
    if type(dimension) is not int or dimension < 0:
        raise ValueError('nonnegative dimension required')
    if any(type(form) is not int or form < 0 or form.bit_length() > dimension
           for form in forms):
        raise ValueError('forms must fit the declared dimension')
    return forms


class _Builder:
    def __init__(self, dimension):
        self.dimension = dimension
        self.next_var = dimension + 1
        self.clauses = []
        self.gates = []

    def fresh(self):
        value = self.next_var
        self.next_var += 1
        return value

    def constant(self, value):
        if value not in (0, 1):
            raise ValueError('Boolean constant required')
        output = self.fresh()
        self.clauses.append([output if value else -output])
        self.gates.append(['const', output, value])
        return output

    def xor(self, left, right):
        output = self.fresh()
        # output = left XOR right
        self.clauses.extend([
            [-left, -right, -output],
            [-left, right, output],
            [left, -right, output],
            [left, right, -output],
        ])
        self.gates.append(['xor', output, left, right])
        return output

    def and_gate(self, left, right):
        output = self.fresh()
        # output = left AND right
        self.clauses.extend([
            [-left, -right, output],
            [left, -output],
            [right, -output],
        ])
        self.gates.append(['and', output, left, right])
        return output

    def not_gate(self, value):
        output = self.fresh()
        self.clauses.extend([[-value, -output], [value, output]])
        self.gates.append(['not', output, value])
        return output

    def or_gate(self, left, right):
        output = self.fresh()
        self.clauses.extend([[-left, output], [-right, output],
                             [left, right, -output]])
        self.gates.append(['or', output, left, right])
        return output

    def parity(self, form):
        inputs = [1 + bit for bit in range(self.dimension) if form >> bit & 1]
        if not inputs:
            return self.constant(0)
        output = inputs[0]
        for input_var in inputs[1:]:
            output = self.xor(output, input_var)
        return output


def _base_builder(forms, dimension):
    forms = _validate_forms(forms, dimension)
    builder = _Builder(dimension)
    parity_outputs = [builder.parity(form) for form in forms]
    width = max(1, len(forms).bit_length())
    accumulator = [builder.constant(0) for _ in range(width)]
    for incoming in parity_outputs:
        carry = incoming
        next_accumulator = []
        for old in accumulator:
            next_accumulator.append(builder.xor(old, carry))
            carry = builder.and_gate(old, carry)
        accumulator = next_accumulator
    return forms, builder, accumulator, width


def _package(forms, dimension, builder, accumulator, width, comparator=None):
    return {
        'dimension': dimension,
        'forms': list(forms),
        'clauses': [list(clause) for clause in builder.clauses],
        'gates': [list(gate) for gate in builder.gates],
        'output_bits': list(accumulator),
        'variables': builder.next_var - 1,
        # CNF literals are one-based, while boundary_dp orders variables by
        # their zero-based internal indices.
        'order': list(range(builder.next_var - 1)),
        'width': width,
        'gate_counts': {
            'constant_gates': sum(gate[0] == 'const' for gate in builder.gates),
            'xor_gates': sum(gate[0] == 'xor' for gate in builder.gates),
            'and_gates': sum(gate[0] == 'and' for gate in builder.gates),
            'not_gates': sum(gate[0] == 'not' for gate in builder.gates),
            'or_gates': sum(gate[0] == 'or' for gate in builder.gates),
            'total_gates': len(builder.gates),
        },
        **({'comparator': comparator} if comparator is not None else {}),
    }


def build_circuit(forms, dimension):
    """Build source parity rows followed by an L-bit ripple accumulator."""
    forms, builder, accumulator, width = _base_builder(forms, dimension)
    return _package(forms, dimension, builder, accumulator, width)


def build_threshold_circuit(forms, dimension, threshold):
    """Build the base circuit plus an O(width) ripple ``output <= threshold`` test."""
    if type(threshold) is not int or threshold < 0:
        raise ValueError('nonnegative threshold required')
    forms, builder, accumulator, width = _base_builder(forms, dimension)
    equal = builder.constant(1)
    less = builder.constant(0)
    for bit, variable in reversed(list(enumerate(accumulator))):
        if (threshold >> bit) & 1:
            less = builder.or_gate(less, builder.and_gate(equal, builder.not_gate(variable)))
            equal = builder.and_gate(equal, variable)
        else:
            equal = builder.and_gate(equal, builder.not_gate(variable))
    accept = builder.or_gate(less, equal)
    builder.clauses.append([accept])
    return _package(forms, dimension, builder, accumulator, width,
                    comparator={'threshold': threshold, 'accept_variable': accept})


def pin_variables(clauses, variables, values):
    variables, values = tuple(variables), tuple(values)
    if len(variables) != len(values) or any(value not in (0, 1) for value in values):
        raise ValueError('variables and Boolean values must have equal length')
    return [list(clause) for clause in clauses] + [
        [variable if value else -variable]
        for variable, value in zip(variables, values)]


def pin_integer(clauses, variables, value):
    if type(value) is not int or value < 0 or value >= (1 << len(tuple(variables))):
        raise ValueError('integer does not fit output variables')
    variables = tuple(variables)
    return pin_variables(clauses, variables,
                         [(value >> bit) & 1 for bit in range(len(variables))])


def at_most(clauses, variables, threshold):
    """Add an exact finite-width CNF comparator: binary output <= threshold."""
    variables = tuple(variables)
    if type(threshold) is not int or threshold < 0:
        raise ValueError('nonnegative threshold required')
    limit = 1 << len(variables)
    if threshold >= limit - 1:
        return [list(clause) for clause in clauses]
    output = [list(clause) for clause in clauses]
    for value in range(threshold + 1, limit):
        output.append([variable if not (value >> bit) & 1 else -variable
                       for bit, variable in enumerate(variables)])
    return output


def evaluate_gates(circuit, assignment):
    """Evaluate source and gate variables from a source assignment."""
    dimension = circuit['dimension']
    if type(assignment) is not int or assignment < 0 or assignment >= (1 << dimension):
        raise ValueError('assignment does not fit source dimension')
    values = {1 + bit: (assignment >> bit) & 1 for bit in range(dimension)}
    for gate in circuit['gates']:
        if gate[0] == 'const':
            values[gate[1]] = gate[2]
        elif gate[0] == 'xor':
            values[gate[1]] = values[gate[2]] ^ values[gate[3]]
        elif gate[0] == 'and':
            values[gate[1]] = values[gate[2]] & values[gate[3]]
        elif gate[0] == 'not':
            values[gate[1]] = 1 ^ values[gate[2]]
        elif gate[0] == 'or':
            values[gate[1]] = values[gate[2]] | values[gate[3]]
        else:
            raise ValueError('unknown gate kind')
    return values


def clauses_satisfied(clauses, assignment):
    return all(any((literal > 0) == bool(assignment[abs(literal)])
                   for literal in clause) for clause in clauses)
