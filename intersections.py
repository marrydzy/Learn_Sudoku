# -*- coding: UTF-8 -*-

""" 'INTERSECTIONS' CLASS OF SOLVING METHODS
    GLOBAL FUNCTIONS:
        locked_candidates() - solving technique that uses the intersections between lines and boxes

TODO:
"""

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_BOX, CELL_ROW, CELL_COL, CELLS_IN_BOX, SUDOKU_VALUES_SET
from utils import get_stats, set_remaining_candidates, eliminate_options


@get_stats
def locked_candidates(solver_status, board, window):
    """ A solving technique that uses the intersections between lines and boxes.
    Aliases include: Intersection Removal, Line-Box Interaction.
    The terms Pointing and Claiming/Box-Line Reduction are often used to distinguish the 2 types.
    This is a basic solving technique. When all candidates for a digit in a house
    are located inside the intersection with another house, we can eliminate the remaining candidates
    from the second house outside the intersection.
    """

    def _paint_locked_candidates(house, locked_candidate):
        return {cell: {(locked_candidate, "cyan"), } for cell in house if locked_candidate in board[cell]}

    def _type_1():
        """ Type 1 (Pointing)
        All the candidates for digit X in a box are confined to a single line (row or column).
        The surplus candidates are eliminated from the part of the line that does not intersect with this box.
        Rating: 50
        """
        for house in CELLS_IN_BOX:
            candidates = SUDOKU_VALUES_SET - {board[cell] for cell in house if len(board[cell]) == 1}
            unsolved = {cell for cell in house if len(board[cell]) > 1}
            for possibility in candidates:
                in_rows = set(CELL_ROW[cell] for cell in unsolved if possibility in board[cell])
                in_cols = set(CELL_COL[cell] for cell in unsolved if possibility in board[cell])
                impacted_cells = None
                if len(in_rows) == 1:
                    impacted_cells = set(CELLS_IN_ROW[in_rows.pop()]).difference(house)
                elif len(in_cols) == 1:
                    impacted_cells = set(CELLS_IN_COL[in_cols.pop()]).difference(house)
                if impacted_cells:
                    to_eliminate = {(possibility, cell) for cell in impacted_cells if possibility in board[cell]}
                    if to_eliminate:
                        if window:
                            solver_status.capture_baseline(board, window)
                        eliminate_options(solver_status, board, to_eliminate, window)
                        locked_candidates.clues += len(solver_status.naked_singles)
                        locked_candidates.options_removed += len(to_eliminate)
                        kwargs["solver_tool"] = "locked_candidates_type_1"
                        if window:
                            window.options_visible = window.options_visible.union(house).union(impacted_cells)
                            kwargs["house"] = impacted_cells.union(house)
                            kwargs["eliminate"] = to_eliminate
                            kwargs["chain_a"] = _paint_locked_candidates(house, possibility)
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
                candidates = SUDOKU_VALUES_SET - {board[cell] for cell in house if len(board[cell]) == 1}
                unsolved = {cell for cell in house if len(board[cell]) > 1}
                for possibility in candidates:
                    boxes = {CELL_BOX[cell] for cell in unsolved if possibility in board[cell]}
                    if len(boxes) == 1:
                        impacted_cells = set(CELLS_IN_BOX[boxes.pop()]).difference(house)
                        to_eliminate = {(possibility, cell) for cell in impacted_cells if possibility in board[cell]}
                        if to_eliminate:
                            if window:
                                solver_status.capture_baseline(board, window)
                            eliminate_options(solver_status, board, to_eliminate, window)
                            locked_candidates.clues += len(solver_status.naked_singles)
                            locked_candidates.options_removed += len(to_eliminate)
                            kwargs["solver_tool"] = "locked_candidates_type_2"
                            if window:
                                window.options_visible = window.options_visible.union(house).union(impacted_cells)
                                kwargs["house"] = impacted_cells.union(house)
                                kwargs["eliminate"] = to_eliminate
                                kwargs["chain_a"] = _paint_locked_candidates(house, possibility)
                            return True
        return False

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    if _type_1() or _type_2():
        return kwargs
    return None
