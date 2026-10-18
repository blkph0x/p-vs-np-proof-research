"""Polynomial homogeneous minimum-distance solver for column weight <= 2."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import inf
from pathlib import Path


ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class DegreeTwoInstance:
    rows: int
    columns: tuple


def encode(rows, columns):
    if type(rows) is not int or rows < 0:
        raise ValueError('rows must be a nonnegative integer')
    normalized = []
    for column in columns:
        if type(column) is not int or column < 0 or column >> rows:
            raise ValueError('column is outside the row space')
        if column.bit_count() > 2:
            raise ValueError('column weight exceeds two')
        if column.bit_count() == 2:
            bits = [i for i in range(rows) if column >> i & 1]
            if bits[0] == bits[1]:
                raise ValueError('repeated row in a weight-two column')
        normalized.append(column)
    return DegreeTwoInstance(rows, tuple(normalized))


def column_rows(column):
    return tuple(i for i in range(column.bit_length()) if column >> i & 1)


def graph_parts(instance):
    ordinary = []
    terminals = []
    zero_columns = []
    adjacency = [[] for _ in range(instance.rows)]
    for index, column in enumerate(instance.columns):
        rows = column_rows(column)
        if len(rows) == 0:
            zero_columns.append(index)
        elif len(rows) == 1:
            terminals.append((index, rows[0]))
        else:
            u, v = rows
            ordinary.append((index, u, v))
            adjacency[u].append((v, index))
            adjacency[v].append((u, index))
    return ordinary, terminals, zero_columns, adjacency


def shortest_path(adjacency, source, target, forbidden_edge=None):
    if source == target:
        return []
    parent = {source: (None, None)}
    queue = deque([source])
    while queue:
        vertex = queue.popleft()
        for neighbor, edge_index in adjacency[vertex]:
            if edge_index == forbidden_edge or neighbor in parent:
                continue
            parent[neighbor] = (vertex, edge_index)
            if neighbor == target:
                path = []
                current = target
                while parent[current][0] is not None:
                    previous, edge = parent[current]
                    path.append(edge)
                    current = previous
                return list(reversed(path))
            queue.append(neighbor)
    return None


def shortest_cycle(adjacency, ordinary):
    best = None
    for edge_index, u, v in ordinary:
        path = shortest_path(adjacency, u, v, forbidden_edge=edge_index)
        if path is None:
            continue
        candidate = path + [edge_index]
        if best is None or len(candidate) < len(best):
            best = candidate
    return best


def solve(instance):
    ordinary, terminals, zero_columns, adjacency = graph_parts(instance)
    if zero_columns:
        return {'status': 'EXACT', 'distance': 1,
                'kind': 'zero_column', 'selected_columns': [zero_columns[0]]}

    best = None
    cycle = shortest_cycle(adjacency, ordinary)
    if cycle is not None:
        best = {'status': 'EXACT', 'distance': len(cycle), 'kind': 'cycle',
                'selected_columns': cycle}

    for left, (left_index, left_vertex) in enumerate(terminals):
        for right_index, right_vertex in terminals[left + 1:]:
            path = shortest_path(adjacency, left_vertex, right_vertex)
            if path is None:
                continue
            candidate = [left_index, right_index] + path
            candidate.sort()
            record = {'status': 'EXACT', 'distance': len(candidate),
                      'kind': 'terminal_path', 'selected_columns': candidate,
                      'terminal_columns': [left_index, right_index]}
            if best is None or record['distance'] < best['distance']:
                best = record

    if best is None:
        return {'status': 'EXACT', 'distance': None, 'kind': 'zero_only',
                'selected_columns': []}
    return best


def syndrome(instance, selected_columns):
    value = 0
    for index in selected_columns:
        value ^= instance.columns[index]
    return value


def verify_solution(instance, solution):
    if solution.get('status') != 'EXACT':
        return False
    selected = solution.get('selected_columns', [])
    if len(selected) != len(set(selected)) or any(index < 0 or index >= len(instance.columns)
                                                   for index in selected):
        return False
    if syndrome(instance, selected) != 0:
        return False
    distance = solution.get('distance')
    if distance is None:
        return selected == []
    return distance == len(selected) and distance > 0

