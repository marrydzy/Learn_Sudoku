# -*- coding: UTF-8 -*-

""" 'SUBSETS' CLASS OF SOLVING METHODS

    GLOBAL FUNCTIONS:
        hidden_pair() - 'Hidden Pair' sudoku solving strategy
        hidden_triplet() - 'Hidden Triplet' sudoku solving strategy
        hidden_quad() - 'Hidden Quad' sudoku solving strategy
        naked_pair() - 'Naked Pair' sudoku solving strategy
        naked_triplet() - 'Naked Triplet' sudoku solving strategy
        naked_quad() - 'Naked Quad' sudoku solving strategy

    LOCAL FUNCTIONS:
        _get_chain() - returns chain of cells with subset candidates
        _hidden_subset() - generic algorithm of finding hidden subsets
        _naked_subset() - generic algorithm of finding naked subsets

TODO:

"""

import itertools
from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_BOX, DeadEndException
from utils import get_stats, set_remaining_candidates, eliminate_options, get_subsets, get_impacted_cells


def _get_chain(subset_cells, subset_candidates):
    chain = defaultdict(set)
    for cell in subset_cells:
        for candidate in subset_candidates:
            chain[cell].add((candidate, 'cyan'))
    return chain


def _hidden_subset(solver_status, board, window, subset_size):
    """ Generic technique of finding hidden subsets
    A Hidden Subset is formed when N digits have only candidates in N cells in a house.
    A Hidden Subset is always complemented by a Naked Subset. Because Hidden Subsets are
    sometimes hard to find, players often prefer to look for Naked Subsets only,
    even when their size is greater.
    In a standard Sudoku, the maximum number of empty cells in a house is 9.
    There is no need to look for subsets larger than 4 cells, because the complementary
    subset will always be size 4 or smaller.
    """

    set_remaining_candidates(board, solver_status)
    subset_strategies = {2: (hidden_pair, 70),
                         3: (hidden_triplet, 100),
                         4: (hidden_quad, 150), }

    for cells in (CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_BOX):
        for house in cells:
            unsolved = {cell for cell in house if len(board[cell]) > 1}
            if len(unsolved) <= subset_size:
                continue
            candidates = set("".join(board[cell] for cell in unsolved))
            if len(unsolved) != len(candidates):
                raise DeadEndException

            candidates_positions = {candidate: {cell for cell in unsolved if candidate in board[cell]}
                                    for candidate in candidates}
            for subset in itertools.combinations(candidates, subset_size):
                subset_nodes = {cell for candidate in subset for cell in candidates_positions[candidate]}
                if len(subset_nodes) == subset_size:
                    to_eliminate = {(candidate, cell) for cell in subset_nodes for candidate in board[cell]
                                    if candidate not in subset}
                    if to_eliminate:
                        kwargs = {}
                        if window:
                            solver_status.capture_baseline(board, window)
                        eliminate_options(solver_status, board, to_eliminate, window)
                        subset_strategies[subset_size][0].clues += len(solver_status.naked_singles)
                        subset_strategies[subset_size][0].options_removed += len(to_eliminate)
                        kwargs["solver_tool"] = subset_strategies[subset_size][0].__name__
                        if window:
                            window.options_visible = window.options_visible.union(unsolved)
                            kwargs["chain_a"] = _get_chain(subset_nodes, candidates_positions)
                            kwargs["eliminate"] = to_eliminate
                            kwargs["house"] = house
                        return kwargs
    return None


def _naked_subset(solver_status, board, window, subset_size):
    """ Generic technique of finding naked subsets
    A Naked Subset is formed by N cells in a house with candidates for exactly N digits.
    N is the size of the subset, which must lie between 2 and the number of unsolved cells
    in the house minus 2.
    Since every Naked Subset is complemented by a Hidden Subset, the smallest of both sets
    will be no larger than 4 in a standard sized Sudoku.
    """
    set_remaining_candidates(board, solver_status)
    subset_strategies = {2: (naked_pair, 60),
                         3: (naked_triplet, 80),
                         4: (naked_quad, 120), }
    for house, subset_dict in get_subsets(board, subset_size):
        subset_cells = {cell for cells in subset_dict.values() for cell in cells}
        impacted_cells = get_impacted_cells(board, subset_cells)
        to_eliminate = {(candidate, cell)
                        for cell in impacted_cells for candidate in set(board[cell]).intersection(subset_dict)}
        if to_eliminate:
            kwargs = {}
            if window:
                solver_status.capture_baseline(board, window)
            eliminate_options(solver_status, board, to_eliminate, window)
            subset_strategies[subset_size][0].clues += len(solver_status.naked_singles)
            subset_strategies[subset_size][0].options_removed += len(to_eliminate)
            kwargs["solver_tool"] = subset_strategies[subset_size][0].__name__
            if window:
                window.options_visible = window.options_visible.union(subset_cells).union(impacted_cells)
                kwargs["chain_a"] = _get_chain(subset_cells, subset_dict)
                kwargs["eliminate"] = to_eliminate
                kwargs["house"] = impacted_cells.union(house)
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
    return _hidden_subset(solver_status, board, window, 2)


@get_stats
def hidden_triplet(solver_status, board, window):
    """ A Hidden Triple is a Hidden Subset of size 3.
    When all candidates for 3 digits in a house are limited to only 3 cells,
    these cells must contain these 3 digits.
    Subsequently, all remaining candidates can be removed from these 3 cells.
    Rating: 100
    """
    return _hidden_subset(solver_status, board, window, 3)


@get_stats
def hidden_quad(solver_status, board, window):
    """ Hidden Quad is a Hidden Subset of size 4.
    When all candidates for 4 digits in a house are limited to only 4 cells,
    these cells must contain these 4 digits.
    Subsequently, all remaining candidates can be removed from these 4 cells.
    Rating: 150
    """
    return _hidden_subset(solver_status, board, window, 4)


@get_stats
def naked_pair(solver_status, board, window):
    """ A Naked Pair is a Naked Subset of size 2.
    It is formed by 2 cells that have candidates for only 2 digits
    and are collocated in the same house.
    Rating: 60
    """
    return _naked_subset(solver_status, board, window, 2)


@get_stats
def naked_triplet(solver_status, board, window):
    """ A Naked Triple is a Naked Subset of size 3.
    It is formed by 3 cells that have candidates for only 3 digits
    and are collocated in the same house.
    Rating: 80
    """
    return _naked_subset(solver_status, board, window, 3)


@get_stats
def naked_quad(solver_status, board, window):
    """  A Naked Quad is a Naked Subset of size 4.
    It is formed by 4 cells that have candidates for only 4 digits
    and are collocated in the same house.
    Rating: 120
    """
    return _naked_subset(solver_status, board, window, 4)
