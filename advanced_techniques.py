# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

# import itertools
from collections import defaultdict

# from icecream import ic

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import is_clue, init_options, remove_options
from utils import get_pairs


def y_wings(solver_status, board, window):
    """Remove candidates (options) using XY Wing technique
    (see https://www.learn-sudoku.com/xy-wing.html)"""

    def _find_wings(cell_id):
        a_value, b_value = board[cell_id]
        corners_ax = defaultdict(list)
        corners_bx = defaultdict(list)
        for nbr_cell in ALL_NBRS[cell_id]:
            if len(board[nbr_cell]) == 2:
                if a_value in board[nbr_cell]:
                    x_value = board[nbr_cell].replace(a_value, "")
                    corners_ax[x_value].append(nbr_cell)
                elif b_value in board[nbr_cell]:
                    x_value = board[nbr_cell].replace(b_value, "")
                    corners_bx[x_value].append(nbr_cell)
        wings = [(x_value, cell_id, corner_ax, corner_bx)
                 for x_value in set(corners_ax) & set(corners_bx)
                 for corner_ax in corners_ax[x_value]
                 for corner_bx in corners_bx[x_value]]
        return wings

    def _reduce_xs(wings):
        for wing in wings:
            to_remove = []
            for cell_id in set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]]):
                if wing[0] in board[cell_id]:
                    to_remove.append((wing[0], cell_id))
            if to_remove:
                solver_status.capture_baseline(board, window)
                remove_options(solver_status, board, to_remove, window)
                kwargs["solver_tool"] = "y_wings"
                kwargs["y_wing"] = wing
                kwargs["remove"] = to_remove
                kwargs["impacted_cells"] = set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]])
                """
                if window:
                    if window.draw_board(board, "y_wings", y_wing=wing, remove=to_remove,
                                         impacted_cells=set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]])):
                        pass
                    else:
                        solver_status.restore_baseline(board, window)
                """
                return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for cell in range(81):
        if len(board[cell]) == 2 and _reduce_xs(_find_wings(cell)):
            return kwargs
    return kwargs


def unique_rectangles(solver_status, board, window):
    """Remove candidates (options) using Unique Rectangle technique
    (see https://www.learn-sudoku.com/unique-rectangle.html)"""

    # 'pairs' data structure:
    # {'xy': [(row, col, blk), ...]}

    # Finding unique rectangles:
    #  - a pair is in at least three cells and the pair values are in options of the fourth one
    #  - the pair is in exactly two rows, to columns and two blocks

    def _reduce_rectangle(pair, corners):
        if all(board[corner] == pair for corner in corners):
            return False
        to_remove = []
        for corner in corners:
            if board[corner] != pair:
                subset = [cell for cell in rect if len(board[cell]) == 2]
                if pair[0] in board[corner]:
                    to_remove.append((pair[0], corner))
                if pair[1] in board[corner]:
                    to_remove.append((pair[1], corner))
                if to_remove:
                    solver_status.capture_baseline(board, window)
                    remove_options(solver_status, board, to_remove, window)
                    if window:
                        window.options_visible = window.options_visible.union(set(corners))
                    kwargs["solver_tool"] = "unique_rectangles"
                    kwargs["rectangle"] = rect
                    kwargs["remove"] = to_remove
                    kwargs["subset"] = subset
                    return True
        return False

    kwargs = {}
    pairs = defaultdict(list)
    for i in range(81):
        if len(board[i]) == 2:
            pairs[board[i]].append((CELL_ROW[i], CELL_COL[i], CELL_SQR[i]))

    for pair, positions in pairs.items():
        if len(positions) > 2:
            rows = list(set(pos[0] for pos in positions))
            cols = list(set(pos[1] for pos in positions))
            blocks = set(pos[2] for pos in positions)
            if len(rows) == 2 and len(cols) == 2 and len(blocks) == 2:
                row_1 = CELLS_IN_ROW[rows[0]]
                row_2 = CELLS_IN_ROW[rows[1]]
                rect = sorted([row_1[cols[0]], row_1[cols[1]], row_2[cols[0]], row_2[cols[1]]])
                for val in pair:
                    if not all(val in board[corner] for corner in rect):
                        break
                else:
                    if _reduce_rectangle(pair, rect):
                        return kwargs
    return {}


def swordfish(solver_status, board, window):
    """Remove candidates (options) using Swordfish technique
    (see https://www.learn-sudoku.com/x-wing.html)
    """

    def _find_swordfish(by_row):
        pairs_dict = get_pairs(board, by_row)
        # 'primary' direction: rows for 'by_row' direction, columns otherwise
        # 'secondary' direction: columns for 'by_row' direction, rows otherwise
        value_positions = defaultdict(list)
        for secondary_idxs, pairs in pairs_dict.items():
            for value, primary_idxs in pairs.items():
                if len(primary_idxs) == 1:
                    value_positions[value].append((primary_idxs[0], secondary_idxs[0], secondary_idxs[1]))
        for value, positions in value_positions.items():
            if len(positions) == 3:
                primary_idxs = []
                secondary_idxs = []
                house = []
                for position in positions:
                    primary_idxs.append(position[0])
                    secondary_idxs.append(position[1])
                    secondary_idxs.append(position[2])
                    house.extend(CELLS_IN_ROW[position[0]] if by_row else CELLS_IN_COL[position[0]])
                in_2_places = (secondary_idxs.count(index) == 2 for index in set(secondary_idxs))
                if all(in_2_places):
                    to_remove = []
                    sword = [value, ]
                    in_cells = set()    # TODO - change the name
                    for position in positions:
                        if by_row:
                            sword.append(position[0] * 9 + position[1])
                            sword.append(position[0] * 9 + position[2])
                            in_cells = in_cells.union(set(CELLS_IN_COL[position[1]]))
                            in_cells = in_cells.union(set(CELLS_IN_COL[position[2]]))
                        else:
                            sword.append(position[1] * 9 + position[0])
                            sword.append(position[2] * 9 + position[0])
                            in_cells = in_cells.union(set(CELLS_IN_ROW[position[1]]))
                            in_cells = in_cells.union(set(CELLS_IN_ROW[position[2]]))
                    secondary_idxs = set(secondary_idxs)
                    for index in secondary_idxs:
                        if by_row:
                            other_cells = [CELLS_IN_COL[index][row] for row in range(9)
                                           if len(board[CELLS_IN_COL[index][row]]) > 1 and row not in primary_idxs]
                        else:
                            other_cells = [CELLS_IN_ROW[index][col] for col in range(9)
                                           if len(board[CELLS_IN_ROW[index][col]]) > 1 and col not in primary_idxs]
                        to_remove.extend([(value, cell) for cell in other_cells if value in board[cell]])

                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        if window:
                            window.options_visible = window.options_visible.union(set(house))
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "swordfish"
                        kwargs["singles"] = solver_status.naked_singles
                        kwargs["sword"] = sword
                        kwargs["remove"] = to_remove
                        kwargs["impacted_cells"] = in_cells
                        kwargs["house"] = house
                        return True
        return False

    kwargs = {}
    if _find_swordfish(True):
        return kwargs
    if _find_swordfish(False):
        return kwargs
    return kwargs


def x_wings(solver_status, board, window):
    """Remove candidates (options) using X Wing technique
    (see https://www.learn-sudoku.com/x-wing.html)"""

    def _find_x_wing(by_row):
        pairs_dict = get_pairs(board, by_row)
        # 'primary' direction: rows for 'by_row' direction, columns otherwise
        # 'secondary' direction: columns for 'by_row' direction, rows otherwise
        for secondary_idxs, pairs in pairs_dict.items():
            for value, primary_idxs in pairs.items():
                if len(primary_idxs) == 2:
                    cells = CELLS_IN_COL if by_row else CELLS_IN_ROW
                    impacted_cells = [cells[secondary_idxs[0]][i] for i in range(9) if i not in primary_idxs]
                    impacted_cells.extend([cells[secondary_idxs[1]][i] for i in range(9) if i not in primary_idxs])
                    house = [cell for cell in range(81) if cell in cells[secondary_idxs[0]] or
                             cell in cells[secondary_idxs[1]]]
                    to_remove = [(value, cell) for cell in impacted_cells if value in board[cell]]
                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        if window:
                            window.options_visible = window.options_visible.union(set(house))
                        rows = primary_idxs if by_row else secondary_idxs
                        cols = secondary_idxs if by_row else primary_idxs
                        corners = [value,
                                   rows[0] * 9 + cols[0], rows[0] * 9 + cols[1],
                                   rows[1] * 9 + cols[0], rows[1] * 9 + cols[1]]
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "x_wings"
                        kwargs["singles"] = solver_status.naked_singles
                        kwargs["x_wing"] = corners
                        kwargs["subset"] = [value]
                        kwargs["remove"] = to_remove
                        kwargs["impacted_cells"] = house
                        return True
        return False

    kwargs = {}
    if _find_x_wing(True):
        return kwargs
    if _find_x_wing(False):
        return kwargs
    return kwargs


def finned_x_wing(solver_status, board, window):
    """ TODO """

    def _find_finned_x_wing(by_row, option):
        cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
        for row_1 in range(9):
            r1_cols = set(col for col in range(9) if
                          option in board[cells[row_1][col]] and not is_clue(cells[row_1][col], board, window))
            if len(r1_cols) == 2:
                for row_2 in range(9):
                    if row_2 != row_1:
                        r2_cols = set(col for col in range(9) if option in board[cells[row_2][col]]
                                      and not is_clue(cells[row_2][col], board, window))
                        if r2_cols.issuperset(r1_cols):
                            fin = r2_cols.difference(r1_cols)
                            other_cells = set()
                            house = set()
                            corners = list()
                            if len(fin) == 1:
                                col_1 = r1_cols.pop()
                                col_2 = r1_cols.pop()
                                col_f = fin.pop()
                                if by_row:
                                    box_1 = CELL_SQR[row_2 * 9 + col_1]
                                    box_2 = CELL_SQR[row_2 * 9 + col_2]
                                    box_f = CELL_SQR[row_2 * 9 + col_f]
                                    corners = [option,
                                               row_1 * 9 + col_1, row_1 * 9 + col_2,
                                               row_2 * 9 + col_1, row_2 * 9 + col_f, row_2 * 9 + col_2]
                                    house = set(CELLS_IN_ROW[row_1]).union(set(CELLS_IN_ROW[row_2]))
                                    if box_1 == box_f:
                                        other_cells = set(CELLS_IN_SQR[box_1]).intersection(set(CELLS_IN_COL[col_1]))
                                        other_cells.discard(row_1 * 9 + col_1)
                                        other_cells.discard(row_2 * 9 + col_1)
                                    elif box_2 == box_f:
                                        other_cells = set(CELLS_IN_SQR[box_2]).intersection(set(CELLS_IN_COL[col_2]))
                                        other_cells.discard(row_1 * 9 + col_2)
                                        other_cells.discard(row_2 * 9 + col_2)
                                else:
                                    box_1 = CELL_SQR[col_1 * 9 + row_2]
                                    box_2 = CELL_SQR[col_2 * 9 + row_2]
                                    box_f = CELL_SQR[col_f * 9 + row_2]
                                    corners = [option,
                                               col_1 * 9 + row_1, col_2 * 9 + row_1,
                                               col_1 * 9 + row_2, col_f * 9 + row_2, col_2 * 9 + row_2]
                                    house = set(CELLS_IN_COL[row_1]).union(set(CELLS_IN_COL[row_2]))
                                    if box_f == box_1:
                                        other_cells = set(CELLS_IN_SQR[box_1]).intersection(set(CELLS_IN_ROW[col_1]))
                                        other_cells.discard(col_1 * 9 + row_1)
                                        other_cells.discard(col_1 * 9 + row_2)
                                    elif box_f == box_2:
                                        other_cells = set(CELLS_IN_SQR[box_2]).intersection(set(CELLS_IN_ROW[col_2]))
                                        other_cells.discard(col_2 * 9 + row_1)
                                        other_cells.discard(col_2 * 9 + row_2)
                            if other_cells:
                                to_remove = [(option, cell) for cell in other_cells if option in board[cell]]
                                if to_remove:
                                    # print(f'\n{other_cells = } {to_remove = }')
                                    solver_status.capture_baseline(board, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(house).union(other_cells)
                                    remove_options(solver_status, board, to_remove, window)
                                    kwargs["solver_tool"] = "finned_x_wings"
                                    kwargs["singles"] = solver_status.naked_singles
                                    kwargs["finned_x_wing"] = corners
                                    kwargs["subset"] = [option]
                                    kwargs["remove"] = to_remove
                                    kwargs["house"] = house
                                    kwargs["impacted_cells"] = other_cells
                                    return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for opt in SUDOKU_VALUES_LIST:
        if _find_finned_x_wing(True, opt):
            return kwargs
        if _find_finned_x_wing(False, opt):
            return kwargs
    return kwargs
