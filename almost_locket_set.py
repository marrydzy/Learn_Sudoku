# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from itertools import combinations
from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_SQR, ALL_NBRS
from utils import get_stats, get_subsets, remove_options


def _get_x_values(als_a, als_b, common_values):
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


def _get_c_chain(als_a, als_b, x, z):
    chain_a = defaultdict(set)
    chain_b = defaultdict(set)
    cells_a = {cell for candidate in als_a for cell in als_a[candidate]}
    cells_b = {cell for candidate in als_b for cell in als_b[candidate]}
    for cell in cells_a:
        for candidate in als_a:
            if candidate == x:
                chain_a[cell].add((candidate, 'yellow'))
            elif candidate == z:
                chain_a[cell].add((candidate, 'bisque'))
            else:
                chain_a[cell].add((candidate, 'cyan'))
    for cell in cells_b:
        for candidate in als_b:
            if candidate == x:
                chain_b[cell].add((candidate, 'lime'))
            elif candidate == z:
                chain_b[cell].add((candidate, 'bisque'))
            else:
                chain_b[cell].add((candidate, 'cyan'))
    return chain_b, chain_a


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
        if len(als_a) > 2 or len(als_b) > 2:
            common_values = set(als_a).intersection(als_b)
            impacted_cells = {cell for cell in range(81) if len(board[cell]) > 1}.difference(als_a).difference(als_b)
            if len(common_values) > 1 and impacted_cells:
                for x in _get_x_values(als_a, als_b, common_values):
                    for z in common_values.difference((x,)):
                        common_neighbours = _get_common_neighbours(als_a[z], als_b[z], impacted_cells)
                        if common_neighbours:
                            to_remove = {(z, cell) for cell in common_neighbours if z in board[cell]}
                            if to_remove:
                                cells_a = {cell for candidate in als_a for cell in als_a[candidate]}
                                cells_b = {cell for candidate in als_b for cell in als_b[candidate]}
                                c_chain, d_chain = _get_c_chain(als_a, als_b, x, z)
                                solver_status.capture_baseline(board, window)
                                remove_options(solver_status, board, to_remove, window)
                                if window:
                                    window.options_visible = window.options_visible.union(cells_a).union(
                                        cells_b).union(common_neighbours)
                                return {"solver_tool": "als_xz",
                                        "c_chain": c_chain,
                                        "d_chain": d_chain,
                                        "remove": to_remove,
                                        "impacted_cells": {cell for _, cell in to_remove}, }
    return None

