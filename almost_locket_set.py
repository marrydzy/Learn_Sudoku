# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from itertools import combinations
from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_SQR, ALL_NBRS
from utils import get_stats, get_subsets, remove_options


def _get_restricted_commons(als_a, als_b, common_values):
    x_values = set()
    for x in common_values:
        for cell in als_a[x]:
            if als_b[x].intersection(ALL_NBRS[cell]) != als_b[x]:
                break
        else:
            x_values.add(x)
    return x_values


def _get_common_neighbours(cells_a, cells_b, impacted_cells):
    common_neighbours = impacted_cells
    for cell_a in cells_a:
        for cell_b in cells_b:
            common_neighbours = common_neighbours.intersection(ALL_NBRS[cell_a]).intersection(ALL_NBRS[cell_b])
    return common_neighbours


def _get_c_chain(als_a=None, als_b=None, als_c=None, x=None, y=None, z=None):
    chain_a = defaultdict(set)
    chain_b = defaultdict(set)
    chain_c = defaultdict(set)
    als_es = ((als_a, chain_a), (als_b, chain_b), (als_c, chain_c))
    color_x = 'yellow'
    color_y = 'yellow'
    color_z = 'lime'
    for als, chain in als_es:
        if als:
            cells = {cell for candidate in als for cell in als[candidate]}
            for cell in cells:
                for candidate in als:
                    if candidate == x:
                        chain[cell].add((candidate, color_x))
                    elif candidate == y:
                        chain[cell].add((candidate, color_y))
                    elif candidate == z:
                        chain[cell].add((candidate, color_z))
                    else:
                        chain[cell].add((candidate, 'cyan'))
            color_x = 'lime' if color_x == 'yellow' else 'yellow'
            color_y = 'lime' if color_y == 'yellow' else 'yellow'
            color_z = 'lime' if color_z == 'yellow' else 'yellow'
    return chain_b, chain_a, chain_c


def _get_alses(board):
    alses = []
    for n in range(1, 8):
        n_alses = []
        for als in get_subsets(board, n, als=True):
            if als not in n_alses:
                n_alses.append(als)
        alses.extend(n_alses)
    return alses


@get_stats
def als_xz(solver_status, board, window):
    """  The ALS-XZ rule says that if A and B are Almost Locked Sets (or ALSes),
    and X is restricted common to A and B, then no other common candidate
    (let's call it Z) can appear outside of A and B in a cell that can see
    all the Z candidates in both A and B.
    Note that it doesn't matter whether or not Z is also restricted common to A and B,
    except that if Z is also restricted common, we can remove X as a candidate
    of any cells outside A and B that can see all the X candidates in both A and B.
    That is, each candidate, in turn, gets to play the role of restricted common,
    giving us the chance to eliminate the other candidate from outside cells.
    Rating: 300-350
    """
    als_es = _get_alses(board)
    for als_a, als_b in combinations(als_es, 2):
        common_values = set(als_a).intersection(als_b)
        impacted_cells = {cell for cell in range(81) if len(board[cell]) > 1}.difference(als_a).difference(als_b)
        if len(common_values) > 1 and impacted_cells:
            for x in _get_restricted_commons(als_a, als_b, common_values):
                for z in common_values.difference((x,)):
                    common_neighbours = _get_common_neighbours(als_a[z], als_b[z], impacted_cells)
                    if common_neighbours:
                        to_remove = {(z, cell) for cell in common_neighbours if z in board[cell]}
                        if to_remove:
                            cells_a = {cell for candidate in als_a for cell in als_a[candidate]}
                            cells_b = {cell for candidate in als_b for cell in als_b[candidate]}
                            c_chain, d_chain, _ = _get_c_chain(als_a=als_a, als_b=als_b, x=x, z=z)
                            solver_status.capture_baseline(board, window)
                            remove_options(solver_status, board, to_remove, window)
                            if window:
                                window.options_visible = window.options_visible.union(cells_a).union(
                                    cells_b).union(common_neighbours)
                            # print('\tALS-XZ')
                            return {"solver_tool": "als_xz",
                                    "chain_a": c_chain,
                                    "chain_b": d_chain,
                                    "remove": to_remove,
                                    "impacted_cells": {cell for _, cell in to_remove}, }
    return None


@get_stats
def als_xy_wing(solver_status, board, window):
    """  Say we have three Almost Locked Sets A, B and C.
    Suppose:
        A and C share a restricted common Y,
        B and C share a restricted common Z, and
        Y and Z are different digits.
    Then for any digit X that is distinct from Y and Z and is a common candidate for A and B,
    we can eliminate X from any cell that sees all cells belonging to either A or B and having X as a candidate.
    Rating: 320-350
    """
    als_es = _get_alses(board)
    for als_a, als_b, als_c in combinations(als_es, 3):
        common_values = set(als_a).intersection(als_b).intersection(als_c)
        impacted_cells = {cell for cell in range(81) if len(board[cell]) > 1}.difference(als_a).difference(als_b)
        if common_values and impacted_cells:
            for y in _get_restricted_commons(als_a, als_c, set(als_a).intersection(als_c)):
                for z in _get_restricted_commons(als_b, als_c, set(als_b).intersection(als_c)):
                    if y != z:
                        for x in set(als_a).intersection(als_b).difference({y, z}):
                            common_neighbours = _get_common_neighbours(als_a[x], als_b[x], impacted_cells)
                            if common_neighbours:
                                to_remove = {(x, cell) for cell in common_neighbours if x in board[cell]}
                                if to_remove:
                                    cells_a = {cell for candidate in als_a for cell in als_a[candidate]}
                                    cells_b = {cell for candidate in als_b for cell in als_b[candidate]}
                                    cells_c = {cell for candidate in als_c for cell in als_c[candidate]}
                                    chain_a, chain_b, chain_c = _get_c_chain(als_a=als_a, als_b=als_c, als_c=als_b,
                                                                             x=y, y=z, z=x)
                                    impacted_cells = {cell for _, cell in to_remove}.difference(
                                        cells_a).difference(cells_b).difference(cells_c)
                                    solver_status.capture_baseline(board, window)
                                    remove_options(solver_status, board, to_remove, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(cells_a).union(
                                            cells_b).union(cells_c).union(common_neighbours)
                                    print('\tALS-XY-Wing')
                                    return {"solver_tool": "als_xy_wing",
                                            "chain_a": chain_a,
                                            "chain_b": chain_b,
                                            "chain_c": chain_c,
                                            "remove": to_remove,
                                            "impacted_cells": impacted_cells,
                                            }
    return None
