# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from itertools import combinations
from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_BOX, CELL_ROW, CELL_COL, CELLS_IN_BOX, SUDOKU_VALUES_LIST
from utils import get_stats, set_remaining_candidates, eliminate_options, get_bi_value_cells


@get_stats
def almost_locked_candidates(solver_status, board, window):
    """ TODO """

    def _get_c_chain(locked_cells, locked_candidate):
        chain = defaultdict(set)
        for cell in locked_cells:
            chain[cell].add((locked_candidate, 'cyan'))
        return chain

    bi_value_cells = get_bi_value_cells(board)
    for bi_value, cells in bi_value_cells.items():
        if len(cells) > 2:
            for xy_pair in combinations(cells, 2):
                if CELL_ROW[xy_pair[0]] != CELL_ROW[xy_pair[1]] and \
                        CELL_COL[xy_pair[0]] != CELL_COL[xy_pair[1]] and \
                        CELL_BOX[xy_pair[0]] != CELL_BOX[xy_pair[1]]:
                    line = None
                    box = None
                    row_0 = CELLS_IN_ROW[CELL_ROW[xy_pair[0]]]
                    col_0 = CELLS_IN_COL[CELL_COL[xy_pair[0]]]
                    box_0 = CELLS_IN_BOX[CELL_BOX[xy_pair[0]]]
                    row_1 = CELLS_IN_ROW[CELL_ROW[xy_pair[1]]]
                    col_1 = CELLS_IN_COL[CELL_COL[xy_pair[1]]]
                    box_1 = CELLS_IN_BOX[CELL_BOX[xy_pair[1]]]
                    if set(row_0).intersection(box_1):
                        line = row_0
                        box = box_1
                    elif set(col_0).intersection(box_1):
                        line = col_0
                        box = box_1
                    elif set(row_1).intersection(box_0):
                        line = row_1
                        box = box_0
                    elif set(col_1).intersection(box_0):
                        line = col_1
                        box = box_0

                    if line and box:
                        other_line_cells = {cell for cell in line if cell not in box and cell not in xy_pair}
                        if not {candidate for cell in other_line_cells for candidate in board[cell]}.intersection(
                                bi_value):
                            impacted_cells = {cell for cell in box if cell not in line and cell not in xy_pair}
                            to_eliminate = {(digit, cell) for digit in bi_value for cell in impacted_cells
                                            if digit in board[cell]}
                            if to_eliminate:
                                solver_status.capture_baseline(board, window)
                                eliminate_options(solver_status, board, to_eliminate, window)
                                if window:
                                    window.options_visible = window.options_visible.union(box).union(line)
                                almost_locked_candidates.clues += len(solver_status.naked_singles)
                                almost_locked_candidates.options_removed += len(to_eliminate)
                                # print('\tAlmost Locked Candidates')
                                return {
                                    "solver_tool": "almost_locked_candidates",
                                    "house": box,
                                    "eliminate": to_eliminate,
                                    "c_chain": _get_c_chain(xy_pair, bi_value)}
    return None


@get_stats
def franken_x_wing(solver_status, board, window):
    """ TODO """
    by_row_boxes = {0: (3, 6), 1: (4, 7), 2: (5, 8),
                    3: (0, 6), 4: (1, 7), 5: (2, 8),
                    6: (0, 3), 7: (1, 4), 8: (2, 5), }
    by_col_boxes = {0: (1, 2), 1: (0, 2), 2: (0, 1),
                    3: (4, 5), 4: (3, 5), 5: (3, 4),
                    6: (7, 8), 7: (6, 8), 8: (6, 7), }

    def _find_franken_x_wing(by_row, option):
        cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
        for row in range(9):
            cols_1 = [col for col in range(9) if
                      option in board[cells[row][col]] and len(board[cells[row][col]]) > 1]
            if len(cols_1) == 2:
                corner_1 = cells[row][cols_1[0]]
                corner_2 = cells[row][cols_1[1]]
                if CELL_BOX[corner_1] == CELL_BOX[corner_2]:
                    other_boxes = by_row_boxes[CELL_BOX[corner_1]] if by_row else by_col_boxes[CELL_BOX[corner_1]]
                    for box in other_boxes:
                        if by_row:
                            cols_2 = set(CELL_COL[cell] for cell in CELLS_IN_BOX[box]
                                         if option in board[cell] and len(board[cell]) > 1)
                        else:
                            cols_2 = set(CELL_ROW[cell] for cell in CELLS_IN_BOX[box]
                                         if option in board[cell] and len(board[cell]) > 1)
                        if set(cols_1) == cols_2:
                            if by_row:
                                other_cells = set(CELLS_IN_COL[cols_1[0]]).union(set(CELLS_IN_COL[cols_1[1]]))
                            else:
                                other_cells = set(CELLS_IN_ROW[cols_1[0]]).union(set(CELLS_IN_ROW[cols_1[1]]))
                            other_cells = other_cells.intersection(set(CELLS_IN_BOX[CELL_BOX[corner_1]]))
                            other_cells.discard(corner_1)
                            other_cells.discard(corner_2)
                            house = set(cells[row]).union(set(CELLS_IN_BOX[box]))
                            corners = [option, corner_1, corner_2]
                            corners.extend(cell for cell in CELLS_IN_BOX[box] if option in board[cell])
                            to_eliminate = [(option, cell) for cell in other_cells if option in board[cell]]
                            if to_eliminate:
                                solver_status.capture_baseline(board, window)
                                if window:
                                    window.options_visible = window.options_visible.union(house).union(other_cells)
                                eliminate_options(solver_status, board, to_eliminate, window)
                                kwargs["solver_tool"] = "franken_x_wing"
                                kwargs["singles"] = solver_status.naked_singles
                                kwargs["finned_x_wing"] = corners
                                kwargs["subset"] = [option]
                                kwargs["eliminate"] = to_eliminate
                                kwargs["house"] = house
                                kwargs["impacted_cells"] = other_cells
                                franken_x_wing.clues += len(solver_status.naked_singles)
                                franken_x_wing.options_removed += len(to_eliminate)
                                return True
        return False

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    for opt in SUDOKU_VALUES_LIST:
        if _find_franken_x_wing(True, opt):
            return kwargs
        if _find_franken_x_wing(False, opt):
            return kwargs
    return kwargs
