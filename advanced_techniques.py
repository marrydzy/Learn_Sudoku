# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from itertools import combinations
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

    init_options(board, solver_status)
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

    def _reduce_rectangle(a_pair, corners):
        if all(board[corner] == a_pair for corner in corners):
            return False
        to_remove = []
        for corner in corners:
            if board[corner] != a_pair:
                subset = [cell for cell in rect if len(board[cell]) == 2]
                if a_pair[0] in board[corner]:
                    to_remove.append((a_pair[0], corner))
                if a_pair[1] in board[corner]:
                    to_remove.append((a_pair[1], corner))
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

    init_options(board, solver_status)
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
    """ TODO """

    def _find_swordfish(by_row):
        for opt in SUDOKU_VALUES_LIST:
            primary_units = {}
            cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
            for indx in range(9):
                at_pos = set(CELL_COL[cell] if by_row else CELL_ROW[cell] for cell in cells[indx]
                             if opt in board[cell] and not is_clue(cell, board, solver_status))
                if len(at_pos) == 2:
                    primary_units[indx] = at_pos
            if len(primary_units) == 3:
                secondary_units = set()
                for indx in primary_units:
                    secondary_units = secondary_units.union(primary_units[indx])
                if len(secondary_units) == 3:
                    impacted_cells = set()
                    house = set()
                    cells_t = CELLS_IN_COL if by_row else CELLS_IN_ROW
                    for indx in secondary_units:
                        impacted_cells = impacted_cells.union(set(cells_t[indx]))
                    for indx in primary_units:
                        impacted_cells = impacted_cells.difference(set(cells[indx]))
                        house = house.union(set(cells[indx]))
                    to_remove = [(opt, cell) for cell in impacted_cells if opt in board[cell]]
                    if to_remove:
                        corners = [cell for idx in primary_units for cell in cells[idx] if opt in board[cell]]
                        corners.insert(0, opt)
                        solver_status.capture_baseline(board, window)
                        if window:
                            window.options_visible = window.options_visible.union(set(house))
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "swordfish"
                        kwargs["singles"] = solver_status.naked_singles
                        kwargs["sword"] = corners
                        kwargs["remove"] = to_remove
                        kwargs["impacted_cells"] = impacted_cells
                        kwargs["house"] = house
                        return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    if _find_swordfish(True):
        return kwargs
    if _find_swordfish(False):
        return kwargs
    return kwargs


def finned_swordfish(solver_status, board, window):
    """ TODO """

    def _find_finned_swordfish(by_row):
        for opt in SUDOKU_VALUES_LIST:
            primary_units = {}
            finned = {}
            cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
            for indx in range(9):
                at_pos = set(CELL_COL[cell] if by_row else CELL_ROW[cell] for cell in cells[indx]
                             if opt in board[cell] and not is_clue(cell, board, solver_status))
                if len(at_pos) == 2:
                    primary_units[indx] = at_pos
                elif len(at_pos) in (3, 4):
                    finned[indx] = at_pos
            if len(primary_units) == 2 and finned:
                secondary_units = set()
                for indx in primary_units:
                    secondary_units = secondary_units.union(primary_units[indx])
                if len(secondary_units) == 3:
                    for finned_indx, finned_values in finned.items():
                        boxes_1 = {indx // 3 for indx in secondary_units}
                        boxes_2 = {indx // 3 for indx in secondary_units.union(finned_values)}
                        if boxes_1 == boxes_2:
                            in_units = defaultdict(int)
                            for indx in secondary_units:
                                if indx in list(primary_units.values())[0]:
                                    in_units[indx] += 1
                                if indx in list(primary_units.values())[1]:
                                    in_units[indx] += 1
                                if indx in finned_values:
                                    in_units[indx] += 1
                            if all((in_units[indx] == 2 for indx in secondary_units)):
                                fin = finned_values.difference(secondary_units)
                                fin_cells = [finned_indx * 9 + indx if by_row else indx * 9 + finned_indx
                                             for indx in fin]
                                impacted_cells = set(CELLS_IN_SQR[CELL_SQR[fin_cells[0]]]).difference(set(fin_cells))
                                secondary_cells = set()
                                for indx in secondary_units:
                                    if by_row:
                                        secondary_cells = secondary_cells.union(set(CELLS_IN_COL[indx]))
                                    else:
                                        secondary_cells = secondary_cells.union(set(CELLS_IN_ROW[indx]))
                                impacted_cells = impacted_cells.intersection(secondary_cells)
                                corners = [opt]
                                if by_row:
                                    for indx in primary_units:
                                        for unit in primary_units[indx]:
                                            corners.append(indx * 9 + unit)
                                    for unit in finned_values:
                                        corners.append(finned_indx * 9 + unit)
                                else:
                                    for indx in primary_units:
                                        for unit in primary_units[indx]:
                                            corners.append(unit * 9 + indx)
                                    for unit in finned_values:
                                        corners.append(unit * 9 + finned_indx)
                                for cell in corners[1:]:
                                    impacted_cells.discard(cell)
                                for indx in secondary_units:
                                    if by_row:
                                        impacted_cells.discard(finned_indx * 9 + indx)
                                    else:
                                        impacted_cells.discard(indx * 9 + finned_indx)
                                house = set(cells[list(primary_units.keys())[0]]).union(
                                            set(cells[list(primary_units.keys())[1]])).union(
                                            set(cells[finned_indx]))
                                to_remove = [(opt, cell) for cell in impacted_cells if opt in board[cell]]
                                # print(f'\n{impacted_cells = }\n{to_remove = }')
                                if to_remove:
                                    solver_status.capture_baseline(board, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(set(house))
                                    remove_options(solver_status, board, to_remove, window)
                                    kwargs["solver_tool"] = "finned_swordfish"
                                    kwargs["singles"] = solver_status.naked_singles
                                    kwargs["sword"] = corners
                                    kwargs["remove"] = to_remove
                                    kwargs["impacted_cells"] = impacted_cells
                                    kwargs["house"] = house
                                    print(f'\n{by_row = }')
                                    return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    if _find_finned_swordfish(True):
        return kwargs
    if _find_finned_swordfish(False):
        return kwargs
    return kwargs


def jellyfish(solver_status, board, window):
    """ TODO """

    def _find_jellyfish(by_row):
        for opt in SUDOKU_VALUES_LIST:
            positions = {}
            cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
            for indx_1 in range(9):
                at_pos = set(CELL_COL[cell] if by_row else CELL_ROW[cell] for cell in cells[indx_1]
                             if opt in board[cell] and not is_clue(cell, board, solver_status))
                if 0 < len(at_pos) < 5:
                    positions[indx_1] = at_pos
            if len(positions) > 3:
                for quad in combinations(positions.keys(), 4):
                    indxs_2 = set()
                    for indx in quad:
                        indxs_2 = indxs_2.union(positions[indx])
                    if len(indxs_2) == 4:
                        impacted_cells = set()
                        house = set()
                        cells_t = CELLS_IN_COL if by_row else CELLS_IN_ROW
                        for indx in indxs_2:
                            impacted_cells = impacted_cells.union(set(cells_t[indx]))
                        for indx in quad:
                            impacted_cells = impacted_cells.difference(set(cells[indx]))
                            house = house.union(set(cells[indx]))
                        to_remove = [(opt, cell) for cell in impacted_cells if opt in board[cell]]
                        if to_remove:
                            corners = [cell for idx in quad for cell in cells[idx] if opt in board[cell]]   # TODO - check it!
                            corners.insert(0, opt)
                            solver_status.capture_baseline(board, window)
                            if window:
                                window.options_visible = window.options_visible.union(set(house))
                            remove_options(solver_status, board, to_remove, window)
                            kwargs["solver_tool"] = "jellyfish"
                            kwargs["singles"] = solver_status.naked_singles
                            kwargs["sword"] = corners
                            kwargs["remove"] = to_remove
                            kwargs["impacted_cells"] = impacted_cells
                            kwargs["house"] = house
                            return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    if _find_jellyfish(True):
        return kwargs
    if _find_jellyfish(False):
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

    init_options(board, solver_status)
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
                          option in board[cells[row_1][col]] and not is_clue(cells[row_1][col], board, solver_status))
            if len(r1_cols) == 2:
                for row_2 in range(9):
                    if row_2 != row_1:
                        r2_cols = set(col for col in range(9) if option in board[cells[row_2][col]]
                                      and not is_clue(cells[row_2][col], board, solver_status))
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

    init_options(board, solver_status)
    kwargs = {}
    for opt in SUDOKU_VALUES_LIST:
        if _find_finned_x_wing(True, opt):
            return kwargs
        if _find_finned_x_wing(False, opt):
            return kwargs
    return kwargs


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
                                kwargs["solver_tool"] = "franken_x_wings"
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


def skyscraper(solver_status, board, window):
    """ TODO """

    def _find_skyscraper(by_row, option):
        cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
        for row_1 in range(8):
            cols_1 = set(col for col in range(9) if option in board[cells[row_1][col]]
                         and not is_clue(cells[row_1][col], board, solver_status))
            if len(cols_1) == 2:
                for row_2 in range(row_1+1, 9):
                    cols_2 = set(col for col in range(9) if option in board[cells[row_2][col]]
                                 and not is_clue(cells[row_2][col], board, solver_status))
                    if len(cols_2) == 2 and len(cols_1.union(cols_2)) == 3:
                        different_cols = cols_1.symmetric_difference(cols_2)
                        cl_1_list = sorted(list(cols_1))

                        cl_2_list = sorted(list(cols_2))
                        corners = list()
                        corners.append((row_1, cl_1_list[0]) if cl_1_list[0] not in different_cols else
                                       (row_1, cl_1_list[1]))
                        corners.append((row_1, cl_1_list[0]) if cl_1_list[0] in different_cols else
                                       (row_1, cl_1_list[1]))
                        corners.append((row_2, cl_2_list[0]) if cl_2_list[0] in different_cols else
                                       (row_2, cl_2_list[1]))
                        corners.append((row_2, cl_2_list[0]) if cl_2_list[0] not in different_cols else
                                       (row_2, cl_2_list[1]))
                        if by_row:
                            corners_idx = [corners[i][0] * 9 + corners[i][1] for i in range(4)]
                        else:
                            corners_idx = [corners[i][1] * 9 + corners[i][0] for i in range(4)]
                        impacted_cells = set(ALL_NBRS[corners_idx[1]]).intersection(ALL_NBRS[corners_idx[2]])
                        for corner in corners_idx:
                            impacted_cells.discard(corner)
                        clues = [cell for cell in impacted_cells if is_clue(cell, board, solver_status)]
                        for clue_id in clues:
                            impacted_cells.discard(clue_id)
                        corners_idx.insert(0, option)
                        to_remove = [(option, cell) for cell in impacted_cells if option in board[cell]]  # TODO - check if not set
                        if to_remove:
                            solver_status.capture_baseline(board, window)
                            house = set(cells[row_1]).union(set(cells[row_2]))
                            if window:
                                window.options_visible = window.options_visible.union(house).union(impacted_cells)
                            remove_options(solver_status, board, to_remove, window)
                            kwargs["solver_tool"] = "skyscraper"
                            kwargs["singles"] = solver_status.naked_singles
                            kwargs["skyscraper"] = corners_idx
                            kwargs["subset"] = [option]
                            kwargs["remove"] = to_remove
                            kwargs["house"] = house
                            kwargs["impacted_cells"] = impacted_cells
                            return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for opt in SUDOKU_VALUES_LIST:
        if _find_skyscraper(True, opt):
            return kwargs
        if _find_skyscraper(False, opt):
            return kwargs
    return kwargs


def sue_de_coq(solver_status, board, window):
    """ TODO """

    def _find_sue_de_coq_type_1(box, by_rows):
        for cell_1 in CELLS_IN_SQR[box]:
            if len(board[cell_1]) == 2:
                if by_rows:
                    indexes = [row for row in range((box // 3) * 3, (box // 3) * 3 + 3) if row != CELL_ROW[cell_1]]
                else:
                    indexes = [col for col in range((box % 3) * 3, (box % 3) * 3 + 3) if col != CELL_COL[cell_1]]
                for indx in indexes:
                    cells_b = set(CELLS_IN_SQR[box])
                    cells_1 = set(CELLS_IN_ROW[indx]) if by_rows else set(CELLS_IN_COL[indx])
                    cells_2 = [cell for cell in cells_1.difference(cells_b)
                               if not is_clue(cell, board, solver_status)]
                    cells_3 = [cell for cell in cells_1.intersection(cells_b)
                               if not is_clue(cell, board, solver_status)]
                    cells_4 = [cell for cell in cells_b.difference(cells_1)
                               if not is_clue(cell, board, solver_status)]
                    if len(cells_3) > 1:
                        for cell_2 in cells_2:
                            if len(board[cell_2]) == 2 and not set(board[cell_1]).intersection(set(board[cell_2])):
                                options_12 = set(board[cell_1]).union(set(board[cell_2]))
                                for pair in combinations(cells_3, 2):
                                    if options_12 == set(board[pair[0]]).union(board[pair[1]]):
                                        to_remove = []
                                        for opt in board[cell_1]:
                                            for cell in cells_4:
                                                if cell != cell_1 and opt in board[cell]:
                                                    to_remove.append((opt, cell))
                                        for opt in board[cell_2]:
                                            for cell in cells_1:
                                                if cell != cell_2 and cell != pair[0] and cell != pair[1] \
                                                        and opt in board[cell]:
                                                    to_remove.append((opt, cell))
                                        if to_remove:
                                            solver_status.capture_baseline(board, window)
                                            house = cells_b.union(cells_1)
                                            pattern = {cell_1, cell_2, pair[0], pair[1]}
                                            impacted_cells = set(cells_2).union(set(cells_3)).union(set(cells_4))
                                            impacted_cells.difference(pattern)
                                            if window:
                                                window.options_visible = window.options_visible.union(house).union(
                                                    house)
                                            remove_options(solver_status, board, to_remove, window)
                                            kwargs["solver_tool"] = "sue_de_coq"
                                            kwargs["singles"] = solver_status.naked_singles
                                            kwargs["sue_de_coq"] = pattern
                                            kwargs["remove"] = to_remove
                                            kwargs["house"] = house
                                            kwargs["impacted_cells"] = impacted_cells
                                            kwargs["subset"] = [to_remove[0][0]]
                                            return True
        return False

    def _find_sue_de_coq_type_2(box, by_rows):
        for cell_1 in CELLS_IN_SQR[box]:
            if len(board[cell_1]) == 2:
                if by_rows:
                    indexes = [row for row in range((box // 3) * 3, (box // 3) * 3 + 3) if row != CELL_ROW[cell_1]]
                else:
                    indexes = [col for col in range((box % 3) * 3, (box % 3) * 3 + 3) if col != CELL_COL[cell_1]]
                for indx in indexes:
                    cells_b = set(CELLS_IN_SQR[box])
                    cells_1 = set(CELLS_IN_ROW[indx]) if by_rows else set(CELLS_IN_COL[indx])
                    cells_2 = [cell for cell in cells_1.difference(cells_b)
                               if not is_clue(cell, board, solver_status)]
                    cells_3 = [cell for cell in cells_1.intersection(cells_b)
                               if not is_clue(cell, board, solver_status)]
                    cells_4 = [cell for cell in cells_b.difference(cells_1)
                               if not is_clue(cell, board, solver_status)]
                    if len(cells_3) == 3:
                        for cell_2 in cells_2:
                            if len(board[cell_2]) == 2 and not set(board[cell_1]).intersection(set(board[cell_2])):
                                options_12 = set(board[cell_1]).union(set(board[cell_2]))
                                options_3 = set(board[cells_3[0]]).union(set(board[cells_3[1]])).union(
                                        set(board[cells_3[2]]))
                                if options_3.issuperset(options_12) and len(options_3.difference(options_12)) == 1:
                                    to_remove = []
                                    for opt in board[cell_1]:
                                        for cell in cells_4:
                                            if cell != cell_1 and opt in board[cell]:
                                                to_remove.append((opt, cell))
                                    for opt in board[cell_2]:
                                        for cell in cells_2:
                                            if cell != cell_2 and opt in board[cell]:
                                                to_remove.append((opt, cell))
                                    opt = options_3.difference(options_12).pop()
                                    for cell in set(cells_2).union(set(cells_4)):
                                        if opt in board[cell]:
                                            to_remove.append((opt, cell))
                                    if to_remove:
                                        solver_status.capture_baseline(board, window)
                                        house = cells_b.union(cells_1)
                                        pattern = {cell_1, cell_2}.union(cells_3)
                                        impacted_cells = set(cells_2).union(set(cells_3)).union(set(cells_4))
                                        impacted_cells.difference(pattern)
                                        if window:
                                            window.options_visible = window.options_visible.union(house).union(
                                                house)
                                        remove_options(solver_status, board, to_remove, window)
                                        kwargs["solver_tool"] = "sue_de_coq"
                                        kwargs["singles"] = solver_status.naked_singles
                                        kwargs["sue_de_coq"] = pattern
                                        kwargs["remove"] = to_remove
                                        kwargs["house"] = house
                                        kwargs["impacted_cells"] = impacted_cells
                                        kwargs["subset"] = [to_remove[0][0]]
                                        return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for sqr in range(9):
        if _find_sue_de_coq_type_1(sqr, True):
            return kwargs
        if _find_sue_de_coq_type_2(sqr, True):
            return kwargs
        if _find_sue_de_coq_type_1(sqr, False):
            return kwargs
        if _find_sue_de_coq_type_2(sqr, False):
            return kwargs
    return kwargs
