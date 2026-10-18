"""Bounded coefficient tables and independently replayable residue controls.

Input pairs describe product_i (z**a_i + z**b_i), with nonnegative integer
exponents and multiplicities retained even when a_i == b_i. The producer
stores every completed sparse layer; the verifier checks the recurrence from
external original inputs. No coefficient-isolation shortcut is assumed.
"""
from __future__ import annotations

from hashlib import sha256
from math import lcm


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _request(choices, target, modulus):
    if type(choices) not in (list, tuple):
        raise ValueError("choices must be a list or tuple")
    normalized = []
    for pair in choices:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise ValueError("each factor must have two exponents")
        for value in pair:
            _integer(value, "exponent")
        normalized.append(tuple(pair))
    _integer(target, "target")
    if modulus is not None:
        _integer(modulus, "modulus", 1)
    return tuple(normalized)


def _caps(max_states, max_total_states, max_transitions):
    _integer(max_states, "max_states", 1)
    _integer(max_total_states, "max_total_states", 1)
    _integer(max_transitions, "max_transitions")


def _binding(choices, target, modulus):
    digest = sha256()
    byte_count = 0

    def add(raw):
        nonlocal byte_count
        digest.update(raw)
        byte_count += len(raw)

    def integer(value):
        raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
        add(len(raw).to_bytes(8, "big"))
        add(raw)

    add(b"binary-product-coefficients-v1\0")
    integer(len(choices))
    for a, b in choices:
        integer(a)
        integer(b)
    integer(target)
    add(b"\x00" if modulus is None else b"\x01")
    if modulus is not None:
        integer(modulus)
    return digest.hexdigest(), byte_count


def _statistics(choices, target, modulus, hash_bytes):
    degree = sum(max(pair) for pair in choices)
    return {"factor_count": len(choices), "input_hash_bytes": hash_bytes,
            "input_exponent_bits": sum(value.bit_length() for pair in choices for value in pair),
            "target_bits": target.bit_length(),
            "modulus_bits": 0 if modulus is None else modulus.bit_length(),
            "degree": degree, "degree_bits": degree.bit_length(),
            "completed_factors": 0, "transitions": 0, "states_created": 1,
            "peak_layer_states": 1, "peak_coefficient_bits": 1,
            "peak_state_key_bits": 0}


def verify_choice_witness(choices, target, witness, *, modulus=None):
    """Check the actual original sum; residue witnesses need not equal target."""
    try:
        choices = _request(choices, target, modulus)
        if type(witness) is not dict or set(witness) != {"bits", "total_weight"}:
            raise ValueError("invalid witness fields")
        bits = witness["bits"]
        if type(bits) not in (list, tuple) or len(bits) != len(choices):
            raise ValueError("invalid witness length")
        if any(type(bit) is not int or bit not in (0, 1) for bit in bits):
            raise ValueError("witness bits must be zero or one")
        total = sum(pair[bit] for pair, bit in zip(choices, bits))
        if type(witness["total_weight"]) is not int or witness["total_weight"] != total:
            raise ValueError("witness total does not match original choices")
        if (total != target if modulus is None else (total - target) % modulus != 0):
            raise ValueError("witness does not meet the original query")
        return {"valid": True, "total_weight": total,
                "equals_target": total == target, "errors": []}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return {"valid": False, "errors": [str(exc)]}


def _realizing_witness(choices, target, modulus, layers):
    state = target if modulus is None else target % modulus
    if state not in layers[-1]:
        return None
    bits = [0] * len(choices)
    for i in range(len(choices) - 1, -1, -1):
        for bit, exponent in enumerate(choices[i]):
            previous = state - exponent
            if modulus is not None:
                previous %= modulus
            if previous in layers[i]:
                bits[i], state = bit, previous
                break
        else:
            raise ArithmeticError("completed coefficient layer has no predecessor")
    if state != 0:
        raise ArithmeticError("coefficient witness does not reach the root")
    return {"bits": bits, "total_weight": sum(pair[bit] for pair, bit in zip(choices, bits))}


def build_coefficient_proof(choices, target, *, modulus=None, max_states=4096,
                            max_total_states=100000, max_transitions=1000000):
    """Build full sparse or cyclic coefficients, with explicit work limits.

    EXACT includes complete counted layers. UNKNOWN includes no coefficient,
    decision, witness or proof. states_created counts stored entries, including
    a partial next layer; transitions counts each processed predecessor/choice
    arc, including an arc whose new state hits a storage cap. No final claim is
    inferred from a partial layer. The input description is always read/hashed.
    """
    choices = _request(choices, target, modulus)
    _caps(max_states, max_total_states, max_transitions)
    binding, hash_bytes = _binding(choices, target, modulus)
    stats = _statistics(choices, target, modulus, hash_bytes)
    layers = [{0: 1}]

    def unknown(reason):
        return {"status": "UNKNOWN", "reason": reason, "input_sha256": binding,
                "target_coefficient": None, "attainable": None,
                "witness": None, "certificate": None, "stats": stats}

    for a, b in choices:
        following = {}
        for state, count in layers[-1].items():
            for exponent in (a, b):
                if stats["transitions"] >= max_transitions:
                    return unknown("transition limit reached")
                key = state + exponent
                if modulus is not None:
                    key %= modulus
                stats["transitions"] += 1
                if key not in following:
                    if len(following) >= max_states:
                        return unknown("per-layer state limit reached")
                    if stats["states_created"] >= max_total_states:
                        return unknown("total stored-state limit reached")
                    following[key] = 0
                    stats["states_created"] += 1
                    stats["peak_layer_states"] = max(stats["peak_layer_states"], len(following))
                    stats["peak_state_key_bits"] = max(stats["peak_state_key_bits"], key.bit_length())
                following[key] += count
                stats["peak_coefficient_bits"] = max(stats["peak_coefficient_bits"], following[key].bit_length())
        layers.append(following)
        stats["completed_factors"] += 1
    key = target if modulus is None else target % modulus
    coefficient = layers[-1].get(key, 0)
    witness = _realizing_witness(choices, target, modulus, layers)
    certificate = {"kind": "binary_product_coefficient_v1", "input_sha256": binding,
                   "mode": "sparse" if modulus is None else "cyclic", "modulus": modulus,
                   "layers": [[[key, layer[key]] for key in sorted(layer)] for layer in layers],
                   "target_coefficient": coefficient, "witness": witness}
    return {"status": "EXACT", "reason": None, "input_sha256": binding,
            "target_coefficient": coefficient, "attainable": coefficient > 0,
            "witness": witness, "certificate": certificate, "stats": stats}


def verify_coefficient_proof(choices, target, certificate, *, modulus=None,
                             max_states=4096, max_total_states=100000,
                             max_transitions=1000000):
    """Verify complete sparse recurrences from the external original request.

    This does not call the producer, use its statistics, or trust certificate
    copies of the graph/product. UNKNOWN means this checker exhausted its
    explicit verification limits, and never endorses a final coefficient.
    """
    stats = {"transitions": 0, "states_read": 0, "layers_checked": 0}

    def outcome(status, reason=None, **extra):
        return {"valid": status == "VERIFIED", "status": status,
                "errors": [] if reason is None else [reason], "stats": stats, **extra}

    try:
        choices = _request(choices, target, modulus)
        _caps(max_states, max_total_states, max_transitions)
        binding, _ = _binding(choices, target, modulus)
        fields = {"kind", "input_sha256", "mode", "modulus", "layers", "target_coefficient", "witness"}
        if type(certificate) is not dict or set(certificate) != fields:
            raise ValueError("invalid coefficient-certificate fields")
        if certificate["kind"] != "binary_product_coefficient_v1":
            raise ValueError("unsupported coefficient-certificate kind")
        if certificate["input_sha256"] != binding:
            raise ValueError("certificate is bound to a different original query")
        expected_mode = "sparse" if modulus is None else "cyclic"
        if certificate["mode"] != expected_mode or type(certificate["modulus"]) is not type(modulus) or certificate["modulus"] != modulus:
            raise ValueError("certificate mode differs from external query")
        raw_layers = certificate["layers"]
        if type(raw_layers) not in (list, tuple) or len(raw_layers) != len(choices) + 1:
            raise ValueError("incorrect number of coefficient layers")
        layers = []
        for layer_index, layer in enumerate(raw_layers):
            if type(layer) not in (list, tuple):
                raise ValueError("coefficient layer must be a list or tuple")
            if len(layer) > max_states:
                return outcome("UNKNOWN", "verification per-layer state limit exceeded")
            if stats["states_read"] + len(layer) > max_total_states:
                return outcome("UNKNOWN", "verification total state limit exceeded")
            parsed = {}
            previous = -1
            for entry in layer:
                if type(entry) not in (list, tuple) or len(entry) != 2:
                    raise ValueError("malformed coefficient entry")
                key, count = entry
                _integer(key, "state key")
                _integer(count, "coefficient", 1)
                if count.bit_length() > layer_index + 1:
                    raise ValueError("coefficient exceeds the number of binary prefix choices")
                if key <= previous or (modulus is not None and key >= modulus):
                    raise ValueError("state keys must be distinct, sorted and within the residue range")
                parsed[key], previous = count, key
            stats["states_read"] += len(parsed)
            layers.append(parsed)
        if layers[0] != {0: 1}:
            raise ValueError("coefficient root must be exactly one at exponent zero")
        stats["layers_checked"] = 1
        for i, pair in enumerate(choices):
            required = {}
            for before, multiplicity in layers[i].items():
                for exponent in pair:
                    if stats["transitions"] >= max_transitions:
                        return outcome("UNKNOWN", "verification transition limit reached")
                    after = before + exponent
                    if modulus is not None:
                        after %= modulus
                    stats["transitions"] += 1
                    if after not in required and len(required) >= max_states:
                        return outcome("UNKNOWN", "verification recurrence state limit exceeded")
                    required[after] = required.get(after, 0) + multiplicity
            if required != layers[i + 1]:
                raise ValueError("coefficient layer does not equal the original-input recurrence")
            stats["layers_checked"] += 1
        query_key = target if modulus is None else target % modulus
        coefficient = layers[-1].get(query_key, 0)
        if type(certificate["target_coefficient"]) is not int or certificate["target_coefficient"] != coefficient:
            raise ValueError("claimed target coefficient is incorrect")
        witness = certificate["witness"]
        if coefficient == 0:
            if witness is not None:
                raise ValueError("a zero coefficient cannot have a witness")
        elif not verify_choice_witness(choices, target, witness, modulus=modulus)["valid"]:
            raise ValueError("positive coefficient needs an original-input realizing witness")
        return outcome("VERIFIED", target_coefficient=coefficient,
                       attainable=coefficient > 0, support_size=len(layers[-1]),
                       input_sha256=binding)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return outcome("INVALID", str(exc))


def joint_residue_proof(choices, target, moduli, **limits):
    """One common choice must meet all residues; its modulus is their LCM."""
    if type(moduli) not in (list, tuple):
        raise ValueError("moduli must be a list or tuple")
    for modulus in moduli:
        _integer(modulus, "modulus", 1)
    combined = lcm(*moduli)  # Empty list has lcm one: no congruence constraints.
    result = build_coefficient_proof(choices, target, modulus=combined, **limits)
    return {"moduli": list(moduli), "joint_modulus": combined, "query": result}
