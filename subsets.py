# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

import itertools
from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_SQR
from utils import get_stats, init_options, remove_options, get_subsets, get_impacted_cells


def _get_c_chain(subset_cells, subset_candidates):
    chain = defaultdict(set)
    for cell in subset_cells:
        for candidate in subset_candidates:
            chain[cell].add((candidate, 'cyan'))
    return chain


def _hidden_subset(solver_status, board, window, subset_size, method_name):
    """ Generic technique of finding hidden subsets
    A Hidden Subset is formed when N digits have only candidates in N cells in a house.
    A Hidden Subset is always complemented by a Naked Subset. Because Hidden Subsets are
    sometimes hard to find, players often prefer to look for Naked Subsets only,
    even when their size is greater.
    In a standard Sudoku, the maximum number of empty cells in a house is 9.
    There is no need to look for subsets larger than 4 cells, because the complementary
    subset will always be size 4 or smaller.
    """

    init_options(board, solver_status)
    for cells in (CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_SQR):
        for house in cells:
            unsolved = {cell for cell in house if len(board[cell]) > 1}
            if len(unsolved) <= subset_size:
                continue
            candidates = set("".join(board[cell] for cell in unsolved))

            # assert len(unsolved) == len(candidates)   TODO

            candidates_positions = {candidate: {cell for cell in unsolved if candidate in board[cell]}
                                    for candidate in candidates}
            for subset in itertools.combinations(candidates, subset_size):
                subset_nodes = {cell for candidate in subset for cell in candidates_positions[candidate]}
                if len(subset_nodes) == subset_size:
                    to_remove = {(candidate, cell) for cell in subset_nodes for candidate in board[cell]
                                 if candidate not in subset}
                    if to_remove:
                        c_chain = _get_c_chain(subset_nodes, candidates_positions)
                        solver_status.capture_baseline(board, window)
                        remove_options(solver_status, board, to_remove, window)
                        if window:
                            window.options_visible = window.options_visible.union(unsolved)
                        kwargs = {
                            "solver_tool": method_name,
                            "c_chain": c_chain,
                            "remove": to_remove, }
                        return kwargs
    return None


def _naked_subset(solver_status, board, window, subset_size, method_name):
    """ Generic technique of finding naked subsets
    A Naked Subset is formed by N cells in a house with candidates for exactly N digits.
    N is the size of the subset, which must lie between 2 and the number of unsolved cells
    in the house minus 2.
    Since every Naked Subset is complemented by a Hidden Subset, the smallest of both sets
    will be no larger than 4 in a standard sized Sudoku.
    """
    init_options(board, solver_status)
    for subset_dict in get_subsets(board, subset_size):
        subset_cells = {cell for cells in subset_dict.values() for cell in cells}
        impacted_cells = get_impacted_cells(board, subset_cells)
        to_remove = {(candidate, cell)
                     for cell in impacted_cells for candidate in set(board[cell]).intersection(subset_dict)}
        if to_remove:
            solver_status.capture_baseline(board, window)
            remove_options(solver_status, board, to_remove, window)
            if window:
                window.options_visible = window.options_visible.union(subset_cells).union(impacted_cells)
            kwargs = {
                "solver_tool": method_name,
                "c_chain": _get_c_chain(subset_cells, subset_dict),
                "impacted_cells": {cell for _, cell in to_remove},
                "remove": to_remove, }
            return kwargs
    return None


@get_stats
def hidden_pair(solver_status, board, window):
    """ A Hidden Pair is a Hidden Subset of size 2.
    When all candidates for 2 digits in a house are limited to only 2 cells,
    these cells must contain these 2 digits.
    Subsequently, all remaining candidates can be removed from these 2 cells.
    Rating: 70
    """
    return _hidden_subset(solver_status, board, window, 2, "hidden_pair")


@get_stats
def hidden_triplet(solver_status, board, window):
    """ A Hidden Triple is a Hidden Subset of size 3.
    When all candidates for 3 digits in a house are limited to only 3 cells,
    these cells must contain these 3 digits.
    Subsequently, all remaining candidates can be removed from these 3 cells.
    Rating: 100
    """
    return _hidden_subset(solver_status, board, window, 3, "hidden_triplet")


@get_stats
def hidden_quad(solver_status, board, window):
    """ Hidden Quad is a Hidden Subset of size 4.
    When all candidates for 4 digits in a house are limited to only 4 cells,
    these cells must contain these 4 digits.
    Subsequently, all remaining candidates can be removed from these 4 cells.
    Rating: 150
    """
    return _hidden_subset(solver_status, board, window, 4, "hidden_quad")


@get_stats
def naked_pair(solver_status, board, window):
    """ A Naked Pair is a Naked Subset of size 2.
    It is formed by 2 cells that have candidates for only 2 digits
    and are collocated in the same house.
    Rating: 60
    """
    return _naked_subset(solver_status, board, window, 2, "naked_pair")


@get_stats
def naked_triplet(solver_status, board, window):
    """ A Naked Triple is a Naked Subset of size 3.
    It is formed by 3 cells that have candidates for only 3 digits
    and are collocated in the same house.
    Rating: 80
    """
    return _naked_subset(solver_status, board, window, 3, "naked_triplet")


@get_stats
def naked_quad(solver_status, board, window):
    """  A Naked Quad is a Naked Subset of size 4.
    It is formed by 4 cells that have candidates for only 4 digits
    and are collocated in the same house.
    Rating: 120
    """
    return _naked_subset(solver_status, board, window, 4, "naked_quad")

