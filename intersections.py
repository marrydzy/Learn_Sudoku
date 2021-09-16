# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_BOX, CELL_ROW, CELL_COL, CELLS_IN_BOX
from utils import SUDOKU_VALUES_SET
from utils import get_stats, init_options, remove_options


def _get_c_chain(locked_cells, locked_candidate):
    chain = defaultdict(set)
    for cell in locked_cells:
        chain[cell].add((locked_candidate, 'cyan'))
    return chain


@get_stats
def locked_candidates(solver_status, board, window):
    """ A solving technique that uses the intersections between lines and boxes.
    Aliases include: Intersection Removal, Line-Box Interaction.
    The terms Pointing and Claiming/Box-Line Reduction are often used to distinguish the 2 types.
    This is a basic solving technique. When all candidates for a digit in a house
    are located inside the intersection with another house, we can eliminate the remaining candidates
    from the second house outside the intersection.
    """

    def _type_1():
        """ Type 1 (Pointing)
        All the candidates for digit X in a box are confined to a single line (row or column).
        The surplus candidates are eliminated from the part of the line that does not intersect with this box.
        Rating: 50
        """
        for house in CELLS_IN_BOX:
            options = SUDOKU_VALUES_SET - {board[cell] for cell in house if len(board[cell]) == 1}
            unsolved = {cell for cell in house if len(board[cell]) > 1}
            for a_digit in options:
                in_rows = set(CELL_ROW[cell] for cell in unsolved if a_digit in board[cell])
                in_cols = set(CELL_COL[cell] for cell in unsolved if a_digit in board[cell])
                impacted_cells = set()
                if len(in_rows) == 1:
                    impacted_cells = set(CELLS_IN_ROW[in_rows.pop()]).difference(house)
                elif len(in_cols) == 1:
                    impacted_cells = set(CELLS_IN_COL[in_cols.pop()]).difference(house)
                if impacted_cells:
                    to_remove = {(a_digit, cell) for cell in impacted_cells if a_digit in board[cell]}
                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        remove_options(solver_status, board, to_remove, window)
                        if window:
                            window.options_visible = window.options_visible.union(house).union(impacted_cells)
                        kwargs["solver_tool"] = "locked_candidates_type_1"
                        kwargs["house"] = house
                        kwargs["remove"] = to_remove
                        kwargs["c_chain"] = _get_c_chain({cell for cell in house if a_digit in board[cell]}, a_digit)
                        kwargs["impacted_cells"] = {cell for _, cell in to_remove}
                        locked_candidates.clues += len(solver_status.naked_singles)
                        locked_candidates.options_removed += len(to_remove)
                        return True
        return False

    def _type_2():
        """ Type 2 (Claiming or Box-Line Reduction)
        All the candidates for digit X in a line are confined to a single box.
        The surplus candidates are eliminated from the part of the box that does not intersect with this line.
        Rating: 50 - 60
        """
        for cells in (CELLS_IN_ROW, CELLS_IN_COL):
            for house in cells:
                options = SUDOKU_VALUES_SET - {board[cell] for cell in house if len(board[cell]) == 1}
                unsolved = {cell for cell in house if len(board[cell]) > 1}
                for a_digit in options:
                    boxes = {CELL_BOX[cell] for cell in unsolved if a_digit in board[cell]}
                    if len(boxes) == 1:
                        impacted_cells = set(CELLS_IN_BOX[boxes.pop()]).difference(house)
                        to_remove = {(a_digit, cell) for cell in impacted_cells if a_digit in board[cell]}
                        if to_remove:
                            solver_status.capture_baseline(board, window)
                            remove_options(solver_status, board, to_remove, window)
                            if window:
                                window.options_visible = window.options_visible.union(house).union(impacted_cells)
                            kwargs["solver_tool"] = "locked_candidates_type_2"
                            kwargs["house"] = house
                            kwargs["remove"] = to_remove
                            kwargs["c_chain"] = _get_c_chain({cell for cell in house if a_digit in board[cell]},
                                                             a_digit)
                            kwargs["impacted_cells"] = {cell for _, cell in to_remove}
                            locked_candidates.clues += len(solver_status.naked_singles)
                            locked_candidates.options_removed += len(to_remove)
                            return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    if _type_1() or _type_2():
        return kwargs
    return None


