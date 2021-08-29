# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from itertools import combinations
from collections import defaultdict
from itertools import combinations


from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_BOX, CELL_ROW, CELL_COL, CELLS_IN_BOX
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import get_stats, is_clue, init_options, remove_options
from utils import get_bi_value_cells, get_house_pairs, get_strong_links, get_pair_house


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
                                    box_1 = CELL_BOX[row_2 * 9 + col_1]
                                    box_2 = CELL_BOX[row_2 * 9 + col_2]
                                    box_f = CELL_BOX[row_2 * 9 + col_f]
                                    corners = [option,
                                               row_1 * 9 + col_1, row_1 * 9 + col_2,
                                               row_2 * 9 + col_1, row_2 * 9 + col_f, row_2 * 9 + col_2]
                                    house = set(CELLS_IN_ROW[row_1]).union(set(CELLS_IN_ROW[row_2]))
                                    if box_1 == box_f:
                                        other_cells = set(CELLS_IN_BOX[box_1]).intersection(set(CELLS_IN_COL[col_1]))
                                        other_cells.discard(row_1 * 9 + col_1)
                                        other_cells.discard(row_2 * 9 + col_1)
                                    elif box_2 == box_f:
                                        other_cells = set(CELLS_IN_BOX[box_2]).intersection(set(CELLS_IN_COL[col_2]))
                                        other_cells.discard(row_1 * 9 + col_2)
                                        other_cells.discard(row_2 * 9 + col_2)
                                else:
                                    box_1 = CELL_BOX[col_1 * 9 + row_2]
                                    box_2 = CELL_BOX[col_2 * 9 + row_2]
                                    box_f = CELL_BOX[col_f * 9 + row_2]
                                    corners = [option,
                                               col_1 * 9 + row_1, col_2 * 9 + row_1,
                                               col_1 * 9 + row_2, col_f * 9 + row_2, col_2 * 9 + row_2]
                                    house = set(CELLS_IN_COL[row_1]).union(set(CELLS_IN_COL[row_2]))
                                    if box_f == box_1:
                                        other_cells = set(CELLS_IN_BOX[box_1]).intersection(set(CELLS_IN_ROW[col_1]))
                                        other_cells.discard(col_1 * 9 + row_1)
                                        other_cells.discard(col_1 * 9 + row_2)
                                    elif box_f == box_2:
                                        other_cells = set(CELLS_IN_BOX[box_2]).intersection(set(CELLS_IN_ROW[col_2]))
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
                                    print('\tfinned X-wing')
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
        pairs_dict = get_house_pairs(CELLS_IN_BOX[box_id], board)
        for pair, cells in pairs_dict.items():
            if len(cells) == 2:
                cells_pos = [(CELL_ROW[cells[0]], CELL_COL[cells[1]]),
                             (CELL_ROW[cells[1]], CELL_COL[cells[0]])]
                values = (pair[0], pair[1])
                for value in values:
                    for row, col in cells_pos:
                        col_2 = [CELL_COL[cell] for cell in CELLS_IN_ROW[row]
                                 if value in board[cell] and CELL_BOX[cell] != box_id]
                        row_2 = [CELL_ROW[cell] for cell in CELLS_IN_COL[col]
                                 if value in board[cell] and CELL_BOX[cell] != box_id]
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
            if len(cells) == 2 and CELL_BOX[cells[0]] != CELL_BOX[cells[1]]:
                cells_pos = [(CELL_ROW[cells[0]], CELL_COL[cells[0]]),
                             (CELL_ROW[cells[1]], CELL_COL[cells[1]])]
                values = (pair[0], pair[1])
                for value in values:
                    for row, col in cells_pos:
                        house_2 = set(CELLS_IN_ROW[row]) if by_column else set(CELLS_IN_COL[col])
                        boxes = [box for box in range(9) if set(CELLS_IN_BOX[box]).intersection(house_2)
                                 and not set(CELLS_IN_BOX[box]).intersection(house_1)]
                        for box in boxes:
                            fins = [cell for cell in set(CELLS_IN_BOX[box]).difference(house_2)
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
                                house = house_1.union(set(CELLS_IN_BOX[box]))
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


@get_stats
def xy_wing(solver_status, board, window):
    """ Remove candidates (options) using XY Wing technique:
    For explanation of the technique see e.g.:
    - https://www.learn-sudoku.com/xy-wing.html
    - https://www.sudoku9981.com/sudoku-solving/xy-wing.php
    Rating: 160
    """

    def _get_c_chain(root, wing_x, wing_y):
        z_value = set(board[wing_x]).intersection(set(board[wing_y])).pop()
        x_value = set(board[root]).intersection(set(board[wing_x])).pop()
        y_value = set(board[root]).intersection(set(board[wing_y])).pop()
        return {root: {(x_value, 'lime'), (y_value, 'yellow')},
                wing_x: {(x_value, 'yellow'), (z_value, 'cyan')},
                wing_y: {(y_value, 'lime'), (z_value, 'cyan')}}

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
                             z_value in board[a_cell] and not is_clue(a_cell, board, solver_status)]
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
                    kwargs["impacted_cells"] = {a_cell for _, a_cell in to_remove}
                    xy_wing.rating += 160
                    xy_wing.options_removed += len(to_remove)
                    xy_wing.clues += len(solver_status.naked_singles)
                    # print('\tXY-Wing')
                    return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for cell in range(81):
        if len(board[cell]) == 2 and _find_xy_wing(cell):
            return kwargs
    return kwargs


@get_stats
def xyz_wing(solver_status, board, window):
    """ Remove candidates (options) using XYZ Wing technique:
    For explanation of the technique see e.g.:
    - https://www.sudoku9981.com/sudoku-solving/xyz-wing.php
    Rating: 200-180
    """

    def _get_c_chain(root, wing_x, wing_y):
        z_value = set(board[wing_x]).intersection(set(board[wing_y])).intersection(set(board[root])).pop()
        x_value = set(board[wing_x]).difference({z_value}).pop()
        y_value = set(board[wing_y]).difference({z_value}).pop()
        return {root: {(x_value, 'lime'), (y_value, 'yellow'), (z_value, 'cyan')},
                wing_x: {(x_value, 'yellow'), (z_value, 'cyan')},
                wing_y: {(y_value, 'lime'), (z_value, 'cyan')}}

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
                    kwargs["impacted_cells"] = {a_cell for _, a_cell in to_remove}
                    xyz_wing.rating += 180
                    xyz_wing.options_removed += len(to_remove)
                    xyz_wing.clues += len(solver_status.naked_singles)
                    # print('\tXYZ-Wing')
                    return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for cell in range(81):
        if len(board[cell]) == 3 and _find_xyz_wing(cell):
            return kwargs
    return kwargs


@get_stats
def wxyz_wing(solver_status, board, window):
    """ TODO """

    def _get_possible_wings():
        possible_wings = set()
        for cell in range(81):
            if len(board[cell]) > 1:
                neighbour_cells = {cell_id for cell_id in ALL_NBRS[cell] if len(board[cell_id]) > 1}
                for triplet in combinations(neighbour_cells, 3):
                    quad = (cell, triplet[0], triplet[1], triplet[2])
                    options = set(''.join(board[cell_id] for cell_id in quad))
                    if len(options) == 4:
                        in_boxes = {CELL_BOX[cell_id] for cell_id in quad}
                        if 4 > len(in_boxes) > 1:
                            in_rows = {CELL_ROW[cell_id] for cell_id in quad}
                            in_columns = {CELL_COL[cell_id] for cell_id in quad}
                            if len(in_rows) > 1 and len(in_columns) > 1 and (len(in_rows) < 4 or len(in_columns) < 4):
                                possible_wings.add(quad)
        return possible_wings

    def _get_cells_candidates(cells, common=True):
        candidates = set(board[cells[0]])
        for cell_id in cells[1:]:
            candidates = candidates.intersection(board[cell_id]) if common else candidates.union(board[cell_id])
        return candidates

    def _get_impacted_cells(nodes, z):
        impacted_cells = None
        for node in nodes:
            if z in board[node]:
                impacted_cells = ALL_NBRS[node]
        for node in nodes:
            if z in board[node]:
                impacted_cells = impacted_cells.intersection(ALL_NBRS[node])
        impacted_cells = {cell_id for cell_id in impacted_cells if len(board[cell_id]) > 1}
        return impacted_cells

    def _get_chain(nodes, z):
        chain_a = defaultdict(set)
        for node in nodes:
            chain_a[node] = {(candidate, 'lime') for candidate in board[node] if candidate != z}
            if z in board[node]:
                chain_a[node].add((z, 'cyan'))
        return chain_a

    def _type_1():
        """ Base position may contain 3 candidates (without Z value) or all 4 candidates (including Z).
        Each of the other wing cells contains two candidates, including Z that is common candidate for
        all three cells. Set of the sum of all candidates for the cells is of size 4.
        Rating: 200 (?)
        """
        for wing in wings:
            if len(board[wing[0]]) > 2:
                for cell_id in wing[1:]:
                    if len(set(ALL_NBRS[cell_id]).intersection(wing)) == 3 or len(board[cell_id]) != 2:
                        break
                else:
                    if len(_get_cells_candidates(wing[1:], common=False)) == 4:
                        z = _get_cells_candidates(wing[1:])
                        if len(z) == 1:
                            z = z.pop()
                            if len(board[wing[0]]) == 4 or z not in board[wing[0]]:
                                impacted_cells = _get_impacted_cells(wing, z)
                                if impacted_cells:
                                    to_remove = {(z, cell_id) for cell_id in impacted_cells if z in board[cell_id]}
                                    if to_remove:
                                        solver_status.capture_baseline(board, window)
                                        if window:
                                            window.options_visible = window.options_visible.union(wing).union(
                                                impacted_cells)
                                        remove_options(solver_status, board, to_remove, window)
                                        kwargs["solver_tool"] = "wxyz_wing_type_1"
                                        kwargs["chain_d"] = _get_chain((wing[0],), z)
                                        kwargs["chain_a"] = _get_chain(wing[1:], z)
                                        kwargs["remove"] = to_remove
                                        kwargs["impacted_cells"] = {a_cell for _, a_cell in to_remove}
                                        wxyz_wing.rating += 200
                                        wxyz_wing.options_removed += len(to_remove)
                                        wxyz_wing.clues += len(solver_status.naked_singles)
                                        # print(f'\t{kwargs["solver_tool"]}')
                                        return True
        return False

    def _type_2():
        """ Base position may contain 2 candidates (without Z value) or 3 candidates (if it includes Z).
        Each of the other wing cells contains two candidates and two of the cells belong to the same house
        (row, column, or box). These 2 cells have one common candidate (called W).
        Let 'aLeft' denote set of two candidates from the cells that are different from W value.
        The 'aLeft' set has one common value with the candidates from the third wing cell (that is Z value).
        Let 'aSum' be a sum of 'aLeft' and the candidates from the third wing cell. Base position
        have two candidates from 'aSum' set (without Z) or all three values (if the Base cell have
        Z candidate)
        Rating: 240 (?
        """

        def _get_other_cells(houses):
            node_a, node_b, node_c = None, None, None
            for _, cells in houses.items():
                if len(cells) == 2:
                    node_a = cells.pop()
                    node_b = cells.pop()
                    node_c = set(wing[1:]).difference({node_a, node_b}).pop()
                    break
            return node_a, node_b, node_c

        for wing in wings:
            for cell_id in wing[1:]:
                if len(set(ALL_NBRS[cell_id]).intersection(wing)) == 3 or len(board[cell_id]) != 2:
                    break
            else:
                rows = defaultdict(set)
                columns = defaultdict(set)
                boxes = defaultdict(set)
                for cell_id in wing[1:]:
                    rows[CELL_ROW[cell_id]].add(cell_id)
                    columns[CELL_COL[cell_id]].add(cell_id)
                    boxes[CELL_BOX[cell_id]].add(cell_id)

                if len(rows) == 2:
                    cell_a, cell_b, cell_c = _get_other_cells(rows)
                elif len(columns) == 2:
                    cell_a, cell_b, cell_c = _get_other_cells(columns)
                elif len(boxes) == 2:
                    cell_a, cell_b, cell_c = _get_other_cells(boxes)
                else:
                    continue

                w = set(board[cell_a]).intersection(board[cell_b])
                if len(w) == 1 and not w.intersection(board[cell_c]):
                    w = w.pop()
                    a_left = set(board[cell_a]).union(board[cell_b])
                    a_left.remove(w)
                    z = a_left.intersection(board[cell_c])
                    if len(z) == 1:
                        z = z.pop()
                        a_sum = set(board[cell_a]).union(board[cell_c])
                        if len(a_sum.intersection(board[wing[0]])) == 2 and z not in board[wing[0]] or \
                                len(a_sum.intersection(board[wing[0]])) == 3:
                            impacted_cells = _get_impacted_cells(wing, z)
                            if impacted_cells:
                                to_remove = {(z, cell_id) for cell_id in impacted_cells if z in board[cell_id]}
                                if to_remove:
                                    solver_status.capture_baseline(board, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(wing).union(
                                            impacted_cells)
                                    remove_options(solver_status, board, to_remove, window)
                                    kwargs["solver_tool"] = "wxyz_wing_type_2"
                                    kwargs["chain_d"] = _get_chain((wing[0],), z)
                                    kwargs["chain_a"] = _get_chain(wing[1:], z)
                                    kwargs["remove"] = to_remove
                                    kwargs["impacted_cells"] = {a_cell for _, a_cell in to_remove}
                                    wxyz_wing.rating += 240
                                    wxyz_wing.options_removed += len(to_remove)
                                    wxyz_wing.clues += len(solver_status.naked_singles)
                                    print(f'\t{kwargs["solver_tool"]}: {wing = }, {w = }, {z = }')
                                    return True
        return False

    def _type_3():
        for wing in wings:
            for cell_id in wing[1:]:
                if len(set(ALL_NBRS[cell_id]).intersection(wing)) == 3:
                    break
            else:
                row_subset = set(CELLS_IN_ROW[CELL_ROW[wing[0]]]).intersection(wing[1:])
                column_subset = set(CELLS_IN_COL[CELL_COL[wing[0]]]).intersection(wing[1:])
                box_subset = set(CELLS_IN_BOX[CELL_BOX[wing[0]]]).intersection(wing[1:])
                subset = None
                if len(row_subset) == 2:
                    subset = row_subset
                elif len(column_subset) == 2:
                    subset = column_subset
                elif len(box_subset) == 2:
                    subset = box_subset
                if subset:
                    subset_candidates = set(''.join(board[cell_id] for cell_id in subset))
                    cell_a = subset.pop()
                    cell_b = subset.pop()
                    cell_c = set(wing[1:]).difference({cell_a, cell_b})
                    cell_c = cell_c.pop()
                    z = set(subset_candidates).intersection(board[cell_c])
                    conditions = [bool(len(subset_candidates) == 3),
                                  bool(set(board[cell_a]).issubset(board[cell_b]) or
                                       set(board[cell_b]).issubset(board[cell_a])),
                                  bool(len(board[cell_c]) == 2),
                                  bool(len(z) == 1)]
                    if all(conditions):
                        z = z.pop()
                        w = board[cell_c].replace(z, '')
                        if w in board[wing[0]] and (len(board[wing[0]]) > 2 or z not in board[wing[0]]):
                            impacted_cells = set(ALL_NBRS[cell_c])
                            if z in board[wing[0]]:
                                impacted_cells = impacted_cells.intersection(ALL_NBRS[wing[0]])
                            if z in board[cell_a]:
                                impacted_cells = impacted_cells.intersection(ALL_NBRS[cell_a])
                            if z in board[cell_b]:
                                impacted_cells = impacted_cells.intersection(ALL_NBRS[cell_b])
                            impacted_cells = {cell_id for cell_id in impacted_cells if len(board[cell_id]) > 1}
                            if impacted_cells:
                                to_remove = {(z, cell_id) for cell_id in impacted_cells if z in board[cell_id]}
                                if to_remove:
                                    solver_status.capture_baseline(board, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(wing).union(
                                            impacted_cells)
                                    remove_options(solver_status, board, to_remove, window)
                                    kwargs["solver_tool"] = "wxyz_wing_type_2"   # TODO
                                    kwargs["c_chain"] = {wing[0]: set(), wing[1]: set(), wing[2]: set(), wing[3]: set()} # TODO
                                    kwargs["remove"] = to_remove
                                    kwargs["impacted_cells"] = {a_cell for _, a_cell in to_remove}
                                    wxyz_wing.rating += 200
                                    wxyz_wing.options_removed += len(to_remove)
                                    wxyz_wing.clues += len(solver_status.naked_singles)
                                    # print(f'\t{kwargs["solver_tool"]}')
                                    return True
        return False

    def _type_4_5():
        for wing in wings:
            base_cells = [wing[0], ]
            for cell_id in wing[1: ]:
                if len(set(ALL_NBRS[cell_id]).intersection(wing)) == 3:
                    base_cells.append(cell_id)
            if len(base_cells) == 2:
                tmp = set(wing).difference(base_cells)
                cell_a = tmp.pop()
                cell_b = tmp.pop()
                z = set(board[cell_a]).intersection(board[cell_b])
                conditions = [bool(len(z) == 1),
                              bool(len(board[cell_a]) == 2 or len(board[cell_b]) == 2),
                              bool(len(board[cell_a]) <= 3 and len(board[cell_b]) <= 3), ]
                if all(conditions):
                    z = z.pop()
                    base_candidates = set(''.join(board[cell_id] for cell_id in base_cells))
                    impacted_cells = set()
                    wing_type = None
                    if len(base_candidates) == 4:
                        impacted_cells = set(ALL_NBRS[wing[0]]).intersection(ALL_NBRS[wing[1]]).intersection(
                            ALL_NBRS[wing[2]].intersection(ALL_NBRS[wing[3]]))
                        wing_type = 'type_2'    # TODO
                    elif len(base_candidates) == 3 and z not in base_candidates:
                        impacted_cells = set(ALL_NBRS[cell_a]).intersection(ALL_NBRS[cell_b])
                        impacted_cells = impacted_cells.difference(wing)
                        wing_type = 'type_2'    # TODO
                    impacted_cells = {cell_id for cell_id in impacted_cells if len(board[cell_id]) > 1}
                    if impacted_cells:
                        to_remove = {(z, cell_id) for cell_id in impacted_cells if z in board[cell_id]}
                        if to_remove:
                            solver_status.capture_baseline(board, window)
                            if window:
                                window.options_visible = window.options_visible.union(wing).union(
                                    impacted_cells)
                            remove_options(solver_status, board, to_remove, window)
                            kwargs["solver_tool"] = "wxyz_wing_" + wing_type
                            kwargs["c_chain"] = {wing[0]: set(), wing[1]: set(), wing[2]: set(), wing[3]: set()} # TODO
                            kwargs["remove"] = to_remove
                            kwargs["impacted_cells"] = {a_cell for _, a_cell in to_remove}
                            wxyz_wing.rating += 200
                            wxyz_wing.options_removed += len(to_remove)
                            wxyz_wing.clues += len(solver_status.naked_singles)
                            # print(f'\t{kwargs["solver_tool"]}')
                            return True
        return False

    kwargs = {}
    wings = _get_possible_wings()

    if _type_1():
        return kwargs
    if _type_2():
        return kwargs
    if _type_3():
        return kwargs
    if _type_4_5():
        return kwargs
    return None


@get_stats
def wxyz_wing_(solver_status, board, window):
    """Remove candidates (options) using WXYZ-Wing technique
    https://www.sudoku9981.com/sudoku-solving/wxyz-wing.php
    """

    def _get_c_chain(nodes, wxyz_values):
        c_chain = defaultdict(set)
        for node in nodes:
            if wxyz_values[1] in board[node] and wxyz_values[2] in board[node]:
                c_chain[node].add((wxyz_values[1], 'lime'))
                c_chain[node].add((wxyz_values[2], 'yellow'))
            elif wxyz_values[1] in board[node]:
                c_chain[node].add((wxyz_values[1], 'yellow'))
            elif wxyz_values[2] in board[node]:
                c_chain[node].add((wxyz_values[2], 'lime'))

            if wxyz_values[0] in board[node]:
                c_chain[node].add((wxyz_values[0], 'moccasin'))
            if wxyz_values[3] in board[node]:
                c_chain[node].add((wxyz_values[3], 'cyan'))
        return c_chain

    def _get_impacted_cells(triplet, fin, z_value):
        impacted_cells = set(ALL_NBRS[fin])
        for node in triplet:
            if z_value in board[node]:
                impacted_cells = impacted_cells.intersection(set(ALL_NBRS[node]))
        return {node for node in impacted_cells if len(board[node]) > 1}

    def _find_wxyz_wing(idx, type, by_row):
        cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
        unsolved = {cell for cell in cells[idx] if len(board[cell]) > 1} if type == 'type_1' \
            else {cell for cell in CELLS_IN_BOX[idx] if len(board[cell]) > 1}
        if len(unsolved) > 3:
            for triplet in combinations(unsolved, 3):
                candidates = set(''.join(board[node] for node in triplet))
                if len(candidates) == 4:
                    house_ids = defaultdict(set)
                    for node in triplet:
                        house_id = CELL_BOX[node] if type == 'type_1' else CELL_ROW[node] if by_row else CELL_COL[node]
                        for value in board[node]:
                            house_ids[value].add(house_id)
                    for value in house_ids:
                        if len(house_ids[value]) == 1:
                            fin_house_id = house_ids[value].pop()
                            other_cells = set(CELLS_IN_BOX[fin_house_id]).difference(cells[idx]) if type == 'type_1' \
                                else set(cells[fin_house_id]).difference(CELLS_IN_BOX[idx])
                            for cell in other_cells:
                                if len(board[cell]) == 2 and value in board[cell] \
                                        and len(set(board[cell]).intersection(candidates)) == 2:
                                    w_value = value
                                    z_value = board[cell].replace(w_value, '')
                                    impacted_cells = _get_impacted_cells(triplet, cell, z_value)
                                    to_remove = [(z_value, node) for node in impacted_cells
                                                 if z_value in board[node]]
                                    if to_remove:   # and type == 'type_2':  TODO - temporary for testing only!
                                        candidates.remove(w_value)
                                        candidates.remove(z_value)
                                        x_value = candidates.pop()
                                        y_value = candidates.pop()
                                        nodes = set(triplet)
                                        nodes.add(cell)
                                        solver_status.capture_baseline(board, window)
                                        if window:
                                            window.options_visible = window.options_visible.union(nodes).union(
                                                impacted_cells)
                                        remove_options(solver_status, board, to_remove, window)
                                        kwargs["solver_tool"] = "wxyz_wing_type_1" if type == 'type_1' else \
                                            "wxyz_wing_type_2"
                                        kwargs["c_chain"] = _get_c_chain(nodes, (w_value, x_value, y_value, z_value))
                                        kwargs["remove"] = to_remove
                                        kwargs["impacted_cells"] = {a_cell for _, a_cell in to_remove}
                                        wxyz_wing.rating += 200
                                        wxyz_wing.options_removed += len(to_remove)
                                        wxyz_wing.clues += len(solver_status.naked_singles)
                                        # if type == 'type_2':
                                        #     print(f'\tWXYZ-Wing')
                                        return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for idx in range(9):
        if _find_wxyz_wing(idx, 'type_1', True):
            break
        if _find_wxyz_wing(idx, 'type_1', False):
            break
        if _find_wxyz_wing(idx, 'type_2', True):
            break
        if _find_wxyz_wing(idx, 'type_2', False):
            break
    return kwargs


def w_wing(solver_status, board, window):
    """Remove candidates (options) using W-Wing technique
    http://hodoku.sourceforge.net/en/tech_wings.php#w
    """

    bi_value_cells = get_bi_value_cells(board)
    strong_links = get_strong_links(board)
    init_options(board, solver_status)
    for pair in bi_value_cells:
        if len(bi_value_cells[pair]) > 1:
            va, vb = pair
            constraint = None
            s_link = None
            for positions in combinations(bi_value_cells[pair], 2):
                for strong_link in strong_links[va]:
                    if not set(positions).intersection(strong_link):
                        sl_a = set(strong_link).intersection(ALL_NBRS[positions[0]])
                        sl_b = set(strong_link).intersection(ALL_NBRS[positions[1]])
                        if sl_a and sl_b and sl_a != sl_b:
                            s_link = strong_link
                            constraint = va
                            break
                if constraint:
                    break
                for strong_link in strong_links[vb]:
                    if not set(positions).intersection(strong_link):
                        sl_a = set(strong_link).intersection(ALL_NBRS[positions[0]])
                        sl_b = set(strong_link).intersection(ALL_NBRS[positions[1]])
                        if sl_a and sl_b and sl_a != sl_b:
                            s_link = strong_link
                            constraint = vb
                            break
                if constraint:
                    break
            else:
                continue
            assert constraint
            other_value = vb if constraint == va else va
            impacted_cells = set(ALL_NBRS[positions[0]]).intersection(ALL_NBRS[positions[1]])
            impacted_cells = {cell for cell in impacted_cells if len(board[cell]) > 1}
            to_remove = [(other_value, cell) for cell in impacted_cells if other_value in board[cell]]
            c_chain = {positions[0]: {(pair[0], 'lime'), (pair[1], 'yellow')},
                       positions[1]: {(pair[0], 'lime'), (pair[1], 'yellow')},
                       s_link[0]: {(constraint, "cyan")}, s_link[1]: {(constraint, 'cyan')}}
            if to_remove:
                kwargs = {}
                solver_status.capture_baseline(board, window)
                if window:
                    window.options_visible = window.options_visible.union(impacted_cells).union(
                        {positions[0], positions[1]}).union(get_pair_house(s_link))
                remove_options(solver_status, board, to_remove, window)
                kwargs["solver_tool"] = "w_wing"
                kwargs["c_chain"] = c_chain
                kwargs["remove"] = to_remove
                kwargs["impacted_cells"] = impacted_cells
                return kwargs
    return {}


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
                if CELL_BOX[corner_1] == CELL_BOX[corner_2]:
                    other_boxes = by_row_boxes[CELL_BOX[corner_1]] if by_row else by_col_boxes[CELL_BOX[corner_1]]
                    for box in other_boxes:
                        if by_row:
                            cols_2 = set(CELL_COL[cell] for cell in CELLS_IN_BOX[box]
                                         if option in board[cell] and not is_clue(cell, board, solver_status))
                        else:
                            cols_2 = set(CELL_ROW[cell] for cell in CELLS_IN_BOX[box]
                                         if option in board[cell] and not is_clue(cell, board, solver_status))
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
