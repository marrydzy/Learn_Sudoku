# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from itertools import combinations
from collections import defaultdict


from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import is_clue, init_options, remove_options
from utils import get_pairs, get_house_pairs


def x_wing(solver_status, board, window):
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


def finned_mutant_x_wing(solver_status, board, window):
    """ TODO """

    def _find_finned_rccb_mutant_x_wing(box_id):
        pairs_dict = get_house_pairs(CELLS_IN_SQR[box_id], board)
        for pair, cells in pairs_dict.items():
            if len(cells) == 2:
                cells_pos = [(CELL_ROW[cells[0]], CELL_COL[cells[1]]),
                             (CELL_ROW[cells[1]], CELL_COL[cells[0]])]
                values = (pair[0], pair[1])
                for value in values:
                    for row, col in cells_pos:
                        col_2 = [CELL_COL[cell] for cell in CELLS_IN_ROW[row]
                                 if value in board[cell] and CELL_SQR[cell] != box_id]
                        row_2 = [CELL_ROW[cell] for cell in CELLS_IN_COL[col]
                                 if value in board[cell] and CELL_SQR[cell] != box_id]
                        if len(col_2) == 1 and len(row_2) == 1:
                            impacted_cell = set(CELLS_IN_COL[col_2[0]]).intersection(set(CELLS_IN_ROW[row_2[0]]))
                            cell = impacted_cell.pop()
                            if value in board[cell]:
                                house = set(CELLS_IN_ROW[row]).union(set(CELLS_IN_COL[col]))
                                impacted_cell = {cell}
                                to_remove = [(value, cell), ]
                                corners = [value, cells[0], cells[1], row * 9 + col_2[0], row_2[0] * 9 + col]
                                solver_status.capture_baseline(board, window)
                                if window:
                                    window.options_visible = window.options_visible.union(house).union(impacted_cell)
                                remove_options(solver_status, board, to_remove, window)
                                kwargs["solver_tool"] = "finned_rccb_mutant_x_wing"
                                kwargs["remove"] = to_remove
                                kwargs["house"] = house
                                kwargs["impacted_cells"] = impacted_cell
                                kwargs["finned_x_wing"] = corners
                                return True
        return False

    def _find_finned_cbrc_mutant_x_wing(by_column, indx):
        house_1 = set(CELLS_IN_COL[indx]) if by_column else set(CELLS_IN_ROW[indx])
        pairs_dict = get_house_pairs(house_1, board)
        for pair, cells in pairs_dict.items():
            if len(cells) == 2 and CELL_SQR[cells[0]] != CELL_SQR[cells[1]]:
                cells_pos = [(CELL_ROW[cells[0]], CELL_COL[cells[0]]),
                             (CELL_ROW[cells[1]], CELL_COL[cells[1]])]
                values = (pair[0], pair[1])
                for value in values:
                    for row, col in cells_pos:
                        house_2 = set(CELLS_IN_ROW[row]) if by_column else set(CELLS_IN_COL[col])
                        boxes = [box for box in range(9) if set(CELLS_IN_SQR[box]).intersection(house_2)
                                 and not set(CELLS_IN_SQR[box]).intersection(house_1)]
                        for box in boxes:
                            fins = [cell for cell in set(CELLS_IN_SQR[box]).difference(house_2)
                                    if value in board[cell] and not is_clue(cell, board, solver_status)]
                            impacted_cell = None
                            if by_column:
                                col_2 = CELL_COL[fins[0]] if fins else None
                                for fin in fins[1:]:
                                    col_2 = col_2 if CELL_COL[fin] == col_2 else None
                                if col_2 is not None:
                                    row_2 = cells_pos[0][0] if row == cells_pos[1][0] else cells_pos[1][0]
                                    impacted_cell = row_2 * 9 + col_2
                            else:
                                row_2 = CELL_ROW[fins[0]] if fins else None
                                for fin in fins[1:]:
                                    row_2 = row_2 if CELL_ROW[fin] == row_2 else None
                                if row_2 is not None:
                                    col_2 = cells_pos[0][1] if col == cells_pos[1][1] else cells_pos[1][1]
                                    impacted_cell = row_2 * 9 + col_2
                            if impacted_cell is not None and value in board[impacted_cell]:
                                house = house_1.union(set(CELLS_IN_SQR[box]))
                                to_remove = [(value, impacted_cell), ]
                                corners = [cell for cell in cells]
                                corners.extend(fins)
                                corners.insert(0, value)
                                solver_status.capture_baseline(board, window)
                                if window:
                                    window.options_visible = window.options_visible.union(house).union({impacted_cell})
                                remove_options(solver_status, board, to_remove, window)
                                kwargs["solver_tool"] = \
                                    "finned_cbrc_mutant_x_wing" if by_column else "finned_rbcc_mutant_x_wing"
                                kwargs["remove"] = to_remove
                                kwargs["house"] = house
                                kwargs["impacted_cells"] = {impacted_cell}
                                kwargs["finned_x_wing"] = corners
                                # if len(fins) > 1:
                                #     print('\nBingo!')
                                return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for i in range(9):
        if _find_finned_rccb_mutant_x_wing(i):
            # print('\nFinned RCCB Mutant X-Wing')
            return kwargs
        if _find_finned_cbrc_mutant_x_wing(True, i):
            # print('\nFinned CBRC Mutant X-Wing')
            return kwargs
        if _find_finned_cbrc_mutant_x_wing(False, i):
            # print('\nFinned RBCC Mutant X-Wing')
            return kwargs
    return kwargs


def xy_wing(solver_status, board, window):
    """ Remove candidates (options) using XY Wing technique:
    For explanation of the technique see e.g.:
    - https://www.learn-sudoku.com/xy-wing.html
    - https://www.sudoku9981.com/sudoku-solving/xy-wing.php
    """

    def _get_c_chain(root, wing_x, wing_y):
        z_value = set(board[wing_x]).intersection(set(board[wing_y])).pop()
        x_value = set(board[root]).intersection(set(board[wing_x])).pop()
        y_value = set(board[root]).intersection(set(board[wing_y])).pop()
        return {root: {(x_value, 'lime'), (y_value, 'yellow')},
                wing_x: {(x_value, 'lime'), (z_value, 'cyan')},
                wing_y: {(y_value, 'yellow'), (z_value, 'cyan')}}

    def _find_xy_wing(cell_id):
        xy = set(board[cell_id])
        bi_values = [indx for indx in ALL_NBRS[cell_id] if len(board[indx]) == 2]
        for pair in combinations(bi_values, 2):
            xz = set(board[pair[0]])
            yz = set(board[pair[1]])
            if len(xy.union(xz).union(yz)) == 3 and not xy.intersection(xz).intersection(yz):
                z_value = xz.intersection(yz).pop()
                impacted_cells = set(ALL_NBRS[pair[0]]).intersection(set(ALL_NBRS[pair[1]]))
                to_remove = [(z_value, a_cell) for a_cell in impacted_cells if
                             z_value in board[a_cell] and not is_clue(cell, board, solver_status)]
                if to_remove:
                    solver_status.capture_baseline(board, window)
                    if window:
                        window.options_visible = window.options_visible.union(impacted_cells).union(
                            {cell_id, pair[0], pair[1]})
                    remove_options(solver_status, board, to_remove, window)
                    kwargs["solver_tool"] = "xy_wing"
                    kwargs["c_chain"] = _get_c_chain(cell_id, pair[0], pair[1])
                    kwargs["edges"] = [(cell_id, pair[0]), (cell_id, pair[1])]
                    kwargs["remove"] = to_remove
                    kwargs["impacted_cells"] = impacted_cells
                    return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for cell in range(81):
        if len(board[cell]) == 2 and _find_xy_wing(cell):
            return kwargs
    return kwargs


def xyz_wing(solver_status, board, window):
    """ Remove candidates (options) using XYZ Wing technique:
    For explanation of the technique see e.g.:
    - https://www.sudoku9981.com/sudoku-solving/xyz-wing.php
    """

    def _get_c_chain(root, wing_x, wing_y):
        z_value = set(board[wing_x]).intersection(set(board[wing_y])).intersection(set(board[root])).pop()
        x_value = set(board[wing_x]).difference({z_value}).pop()
        y_value = set(board[wing_y]).difference({z_value}).pop()
        return {root: {(x_value, 'lime'), (y_value, 'yellow'), (z_value, 'cyan')},
                wing_x: {(x_value, 'lime'), (z_value, 'cyan')},
                wing_y: {(y_value, 'yellow'), (z_value, 'cyan')}}

    def _find_xyz_wing(cell_id):
        xyz = set(board[cell_id])
        bi_values = [indx for indx in ALL_NBRS[cell_id] if len(board[indx]) == 2]
        for pair in combinations(bi_values, 2):
            xz = set(board[pair[0]])
            yz = set(board[pair[1]])
            if xz != yz and len(xyz.union(xz).union(yz)) == 3:
                z_value = xyz.intersection(xz).intersection(yz).pop()
                impacted_cells = set(ALL_NBRS[cell_id]).intersection(set(ALL_NBRS[pair[0]])).intersection(
                                 set(ALL_NBRS[pair[1]]))
                to_remove = [(z_value, a_cell) for a_cell in impacted_cells if
                             z_value in board[a_cell] and not is_clue(cell, board, solver_status)]
                if to_remove:
                    solver_status.capture_baseline(board, window)
                    if window:
                        window.options_visible = window.options_visible.union(impacted_cells).union(
                            {cell_id, pair[0], pair[1]})
                    remove_options(solver_status, board, to_remove, window)
                    kwargs["solver_tool"] = "xyz_wing"
                    kwargs["c_chain"] = _get_c_chain(cell_id, pair[0], pair[1])
                    kwargs["edges"] = [(cell_id, pair[0]), (cell_id, pair[1])]
                    kwargs["remove"] = to_remove
                    kwargs["impacted_cells"] = impacted_cells
                    return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for cell in range(81):
        if len(board[cell]) == 3 and _find_xyz_wing(cell):
            return kwargs
    return kwargs


# TODO - obsolete?
def wxy_wing(solver_status, board, window):
    """ Remove candidates (options) using WXY Wing technique:
    For explanation of the technique see e.g.:
    - https://www.learn-sudoku.com/xy-wing.html
    """

    def _find_wxy_wing(cell_id):
        wxy = set(board[cell_id])
        bi_values = [indx for indx in ALL_NBRS[cell_id] if len(board[indx]) == 2]
        if len(bi_values) > 2:
            for triplet in combinations(bi_values, 3):
                wz = set(board[triplet[0]])
                xz = set(board[triplet[1]])
                yz = set(board[triplet[2]])
                if len(wxy.union(wz).union(xz).union(yz)) == 4 \
                        and len(wz.union(xz).union(yz)) == 4 \
                        and len(wz.intersection(xz).intersection(yz)) == 1 \
                        and not wxy.intersection(wz).intersection(xz).intersection(yz):
                    z_value = wz.intersection(xz).intersection(yz).pop()
                    impacted_cells = set(ALL_NBRS[triplet[0]]).intersection(
                        set(ALL_NBRS[triplet[1]])).intersection(set(ALL_NBRS[triplet[2]]))
                    to_remove = [(z_value, a_cell) for a_cell in impacted_cells if
                                 z_value in board[a_cell] and not is_clue(cell, board, solver_status)]
                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        if window:
                            window.options_visible = window.options_visible.union(set(triplet)).union(impacted_cells)
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "wxy_wing"
                        kwargs["wxy_wing"] = (z_value, cell_id, triplet[0], triplet[1], triplet[2])
                        kwargs["remove"] = to_remove
                        kwargs["impacted_cells"] = impacted_cells
                        return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for cell in range(81):
        if len(board[cell]) == 3 and _find_wxy_wing(cell):
            return kwargs
    return kwargs


def wxyz_wing(solver_status, board, window):
    """Remove candidates (options) using XY Wing technique
    https://www.sudoku9981.com/sudoku-solving/wxyz-wing.php
    """

    def _get_c_chain(nodes, wxyz_values):
        c_chain = defaultdict(set)
        for node in nodes:
            if wxyz_values[0] in board[node]:
                c_chain[node].add((wxyz_values[0], 'moccasin'))
            if wxyz_values[1] in board[node]:
                c_chain[node].add((wxyz_values[1], 'lime'))
            if wxyz_values[2] in board[node]:
                c_chain[node].add((wxyz_values[2], 'yellow'))
            if wxyz_values[3] in board[node]:
                c_chain[node].add((wxyz_values[3], 'cyan'))
        return c_chain

    def _get_impacted_cells(triplet, fin, z_value):
        impacted_cells = set(ALL_NBRS[fin])
        for node in triplet:
            if z_value in board[node]:
                impacted_cells = impacted_cells.intersection(set(ALL_NBRS[node]))
        return {node for node in impacted_cells if len(board[node]) > 1}

    def _find_wxyz_wing_type_1(idx, by_row):
        cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
        unsolved = {cell for cell in cells[idx] if len(board[cell]) > 1}
        if len(unsolved) > 3:
            for triplet in combinations(unsolved, 3):
                candidates = set(''.join(board[node] for node in triplet))
                if len(candidates) == 4:
                    in_boxes = defaultdict(set)
                    for node in triplet:
                        box = CELL_SQR[node]
                        for value in board[node]:
                            in_boxes[value].add(box)
                    for value in in_boxes:
                        if len(in_boxes[value]) == 1:
                            box = in_boxes[value].pop()
                            other_box_cells = set(CELLS_IN_SQR[box]).difference(unsolved)
                            for cell in other_box_cells:
                                if len(board[cell]) == 2 and value in board[cell] \
                                        and len(set(board[cell]).intersection(candidates)) == 2:
                                    w_value = value
                                    z_value = board[cell].replace(w_value, '')
                                    impacted_cells = _get_impacted_cells(triplet, cell, z_value)
                                    to_remove = [(z_value, node) for node in impacted_cells
                                                 if z_value in board[node]]
                                    if to_remove:
                                        candidates.remove(w_value)
                                        candidates.remove(z_value)
                                        x_value = candidates.pop()
                                        y_value = candidates.pop()
                                        nodes = set(triplet).union({cell})
                                        solver_status.capture_baseline(board, window)
                                        if window:
                                            window.options_visible = window.options_visible.union(nodes).union(
                                                impacted_cells)
                                        remove_options(solver_status, board, to_remove, window)
                                        kwargs["solver_tool"] = "wxyz_wing"
                                        kwargs["c_chain"] = _get_c_chain(nodes, (w_value, x_value, y_value, z_value))
                                        kwargs["remove"] = to_remove
                                        kwargs["impacted_cells"] = impacted_cells
                                        return True
        return False

    def _find_wxyz_wing_type_2(idx, by_row):
        cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
        unsolved = {cell for cell in CELLS_IN_SQR[idx] if len(board[cell]) > 1}
        if len(unsolved) > 3:
            for triplet in combinations(unsolved, 3):
                candidates = set(''.join(board[node] for node in triplet))
                if len(candidates) == 4:
                    in_lines = defaultdict(set)
                    for node in triplet:
                        line_id = CELL_ROW[node] if by_row else CELL_COL[node]
                        for value in board[node]:
                            in_lines[value].add(line_id)
                    for value in in_lines:
                        if len(in_lines[value]) == 1:
                            line_idx = in_lines[value].pop()
                            other_line_cells = set(cells[line_idx]).difference(set(CELLS_IN_SQR[idx]))
                            for cell in other_line_cells:
                                if len(board[cell]) == 2 and value in board[cell] \
                                        and len(set(board[cell]).intersection(candidates)) == 2:
                                    w_value = value
                                    z_value = board[cell].replace(w_value, '')
                                    # impacted_cells = set(cells[line_idx]).intersection(unsolved).difference(
                                        # set(triplet))
                                    impacted_cells = _get_impacted_cells(triplet, cell, z_value)
                                    to_remove = [(z_value, node) for node in impacted_cells
                                                 if z_value in board[node]]
                                    if to_remove:
                                        candidates.remove(w_value)
                                        candidates.remove(z_value)
                                        x_value = candidates.pop()
                                        y_value = candidates.pop()
                                        nodes = set(triplet).union({cell})
                                        solver_status.capture_baseline(board, window)
                                        if window:
                                            window.options_visible = window.options_visible.union(nodes).union(
                                                impacted_cells)
                                        remove_options(solver_status, board, to_remove, window)
                                        kwargs["solver_tool"] = "wxyz_wing"
                                        kwargs["c_chain"] = _get_c_chain(nodes, (w_value, x_value, y_value, z_value))
                                        kwargs["remove"] = to_remove
                                        kwargs["impacted_cells"] = impacted_cells
                                        # print('\nwxyz_wing_type_2')
                                        return True

        return False

    init_options(board, solver_status)
    kwargs = {}
    for idx in range(9):
        if _find_wxyz_wing_type_1(idx, True):
            break
        if _find_wxyz_wing_type_1(idx, False):
            break
        if _find_wxyz_wing_type_2(idx, True):
            # print('\nwxyz_wing_type_2 - True')
            break
        if _find_wxyz_wing_type_2(idx, False):
            # print('\nwxyz_wing_type_2 - False')
            break
    return kwargs


# TODO: Obsolete method!
def _wxyz_wing(solver_status, board, window):
    """Remove candidates (options) using XY Wing technique
    (see https://www.learn-sudoku.com/xy-wing.html)"""

    def _find_wxyz_wing(cell_id):
        wxyz = set(board[cell_id])
        bi_values = [indx for indx in ALL_NBRS[cell_id] if len(board[indx]) == 2]
        if len(bi_values) > 2:
            for triplet in combinations(bi_values, 3):
                wz = set(board[triplet[0]])
                xz = set(board[triplet[1]])
                yz = set(board[triplet[2]])
                if len(wxyz.union(wz).union(xz).union(yz)) == 4 \
                        and len(wz.union(xz).union(yz)) == 4 \
                        and len(wz.intersection(xz).intersection(yz)) == 1:
                    z_value = wz.intersection(xz).intersection(yz).pop()
                    impacted_cells = set(ALL_NBRS[cell_id]).intersection(set(ALL_NBRS[triplet[0]])).intersection(
                                     set(ALL_NBRS[triplet[1]])).intersection(set(ALL_NBRS[triplet[2]]))
                    to_remove = [(z_value, a_cell) for a_cell in impacted_cells if
                                 z_value in board[a_cell] and not is_clue(cell, board, solver_status)]
                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        if window:
                            window.options_visible = window.options_visible.union(set(triplet)).union(impacted_cells)
                            window.options_visible.add(cell_id)
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "wxyz_wing"
                        kwargs["wxy_wing"] = (z_value, cell_id, triplet[0], triplet[1], triplet[2])
                        kwargs["remove"] = to_remove
                        kwargs["impacted_cells"] = impacted_cells
                        return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for cell in range(81):
        if len(board[cell]) == 4 and _find_wxyz_wing(cell):
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
