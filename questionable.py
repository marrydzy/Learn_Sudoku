# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR, SUDOKU_VALUES_LIST
from utils import is_clue, init_options, remove_options


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
                      option in board[cells[row][col]] and not is_clue(cells[row][col], board, solver_status)]
            if len(cols_1) == 2:
                corner_1 = cells[row][cols_1[0]]
                corner_2 = cells[row][cols_1[1]]
                if CELL_SQR[corner_1] == CELL_SQR[corner_2]:
                    other_boxes = by_row_boxes[CELL_SQR[corner_1]] if by_row else by_col_boxes[CELL_SQR[corner_1]]
                    for box in other_boxes:
                        if by_row:
                            cols_2 = set(CELL_COL[cell] for cell in CELLS_IN_SQR[box]
                                         if option in board[cell] and not is_clue(cell, board, solver_status))
                        else:
                            cols_2 = set(CELL_ROW[cell] for cell in CELLS_IN_SQR[box]
                                         if option in board[cell] and not is_clue(cell, board, solver_status))
                        if set(cols_1) == cols_2:
                            if by_row:
                                other_cells = set(CELLS_IN_COL[cols_1[0]]).union(set(CELLS_IN_COL[cols_1[1]]))
                            else:
                                other_cells = set(CELLS_IN_ROW[cols_1[0]]).union(set(CELLS_IN_ROW[cols_1[1]]))
                            other_cells = other_cells.intersection(set(CELLS_IN_SQR[CELL_SQR[corner_1]]))
                            other_cells.discard(corner_1)
                            other_cells.discard(corner_2)
                            house = set(cells[row]).union(set(CELLS_IN_SQR[box]))
                            corners = [option, corner_1, corner_2]
                            corners.extend(cell for cell in CELLS_IN_SQR[box] if option in board[cell])
                            to_remove = [(option, cell) for cell in other_cells if option in board[cell]]
                            if to_remove:
                                solver_status.capture_baseline(board, window)
                                if window:
                                    window.options_visible = window.options_visible.union(house).union(other_cells)
                                remove_options(solver_status, board, to_remove, window)
                                kwargs["solver_tool"] = "franken_x_wing"
                                kwargs["singles"] = solver_status.naked_singles
                                kwargs["finned_x_wing"] = corners
                                kwargs["subset"] = [option]
                                kwargs["remove"] = to_remove
                                kwargs["house"] = house
                                kwargs["impacted_cells"] = other_cells
                                return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for opt in SUDOKU_VALUES_LIST:
        if _find_franken_x_wing(True, opt):
            return kwargs
        if _find_franken_x_wing(False, opt):
            return kwargs
    return kwargs
