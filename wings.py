# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from collections import defaultdict
from itertools import combinations


from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_BOX, CELL_ROW, CELL_COL, CELLS_IN_BOX
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import get_stats, is_clue, init_remaining_candidates, eliminate_options
from utils import get_bi_value_cells, get_house_pairs, get_strong_links, get_pair_house


def _get_chain(board, nodes, z, w=None):
    chain = defaultdict(set)
    for node in nodes:
        chain[node] = {(candidate, 'lime') for candidate in board[node] if candidate not in (z, w)}
        if z in board[node]:
            chain[node].add((z, 'cyan'))
        if w and w in board[node]:
            chain[node].add((w, 'moccasin'))
    return chain


@get_stats
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
                                to_eliminate = [(option, cell) for cell in other_cells if option in board[cell]]
                                if to_eliminate:
                                    solver_status.capture_baseline(board, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(house).union(other_cells)
                                    eliminate_options(solver_status, board, to_eliminate, window)
                                    kwargs["solver_tool"] = "finned_x_wings"
                                    kwargs["singles"] = solver_status.naked_singles
                                    kwargs["finned_x_wing"] = corners
                                    kwargs["subset"] = [option]
                                    kwargs["eliminate"] = to_eliminate
                                    kwargs["house"] = house
                                    kwargs["impacted_cells"] = other_cells
                                    finned_x_wing.options_removed += len(to_eliminate)
                                    finned_x_wing.clues += len(solver_status.naked_singles)
                                    # print('\tfinned X-wing')
                                    return True
        return False

    init_remaining_candidates(board, solver_status)
    kwargs = {}
    for opt in SUDOKU_VALUES_LIST:
        if _find_finned_x_wing(True, opt):
            return kwargs
        if _find_finned_x_wing(False, opt):
            return kwargs
    return kwargs


@get_stats
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
                                to_eliminate = [(value, cell), ]
                                corners = [value, cells[0], cells[1], row * 9 + col_2[0], row_2[0] * 9 + col]
                                solver_status.capture_baseline(board, window)
                                if window:
                                    window.options_visible = window.options_visible.union(house).union(impacted_cell)
                                eliminate_options(solver_status, board, to_eliminate, window)
                                kwargs["solver_tool"] = "finned_rccb_mutant_x_wing"
                                kwargs["eliminate"] = to_eliminate
                                kwargs["house"] = house
                                kwargs["impacted_cells"] = impacted_cell
                                kwargs["finned_x_wing"] = corners
                                finned_mutant_x_wing.options_removed += len(to_eliminate)
                                finned_mutant_x_wing.clues += len(solver_status.naked_singles)
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
                                to_eliminate = [(value, impacted_cell), ]
                                corners = [cell for cell in cells]
                                corners.extend(fins)
                                corners.insert(0, value)
                                solver_status.capture_baseline(board, window)
                                if window:
                                    window.options_visible = window.options_visible.union(house).union({impacted_cell})
                                eliminate_options(solver_status, board, to_eliminate, window)
                                kwargs["solver_tool"] = \
                                    "finned_cbrc_mutant_x_wing" if by_column else "finned_rbcc_mutant_x_wing"
                                kwargs["eliminate"] = to_eliminate
                                kwargs["house"] = house
                                kwargs["impacted_cells"] = {impacted_cell}
                                kwargs["finned_x_wing"] = corners
                                finned_mutant_x_wing.options_removed += len(to_eliminate)
                                finned_mutant_x_wing.clues += len(solver_status.naked_singles)
                                # if len(fins) > 1:
                                #     print('\nBingo!')
                                return True
        return False

    init_remaining_candidates(board, solver_status)
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
                to_eliminate = [(z_value, a_cell) for a_cell in impacted_cells if
                                z_value in board[a_cell] and not is_clue(a_cell, board, solver_status)]
                if to_eliminate:
                    solver_status.capture_baseline(board, window)
                    if window:
                        window.options_visible = window.options_visible.union(impacted_cells).union(
                            {cell_id, pair[0], pair[1]})
                    eliminate_options(solver_status, board, to_eliminate, window)
                    kwargs["solver_tool"] = "xy_wing"
                    kwargs["c_chain"] = _get_c_chain(cell_id, pair[0], pair[1])
                    kwargs["edges"] = [(cell_id, pair[0]), (cell_id, pair[1])]
                    kwargs["eliminate"] = to_eliminate
                    kwargs["impacted_cells"] = {a_cell for _, a_cell in to_eliminate}
                    xy_wing.options_removed += len(to_eliminate)
                    xy_wing.clues += len(solver_status.naked_singles)
                    # print('\tXY-Wing')
                    return True
        return False

    init_remaining_candidates(board, solver_status)
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
                to_eliminate = [(z_value, a_cell) for a_cell in impacted_cells if
                                z_value in board[a_cell] and not is_clue(cell, board, solver_status)]
                if to_eliminate:
                    solver_status.capture_baseline(board, window)
                    if window:
                        window.options_visible = window.options_visible.union(impacted_cells).union(
                            {cell_id, pair[0], pair[1]})
                    eliminate_options(solver_status, board, to_eliminate, window)
                    kwargs["solver_tool"] = "xyz_wing"
                    kwargs["c_chain"] = _get_c_chain(cell_id, pair[0], pair[1])
                    kwargs["edges"] = [(cell_id, pair[0]), (cell_id, pair[1])]
                    kwargs["eliminate"] = to_eliminate
                    kwargs["impacted_cells"] = {a_cell for _, a_cell in to_eliminate}
                    xyz_wing.options_removed += len(to_eliminate)
                    xyz_wing.clues += len(solver_status.naked_singles)
                    # print('\tXYZ-Wing')
                    return True
        return False

    init_remaining_candidates(board, solver_status)
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

    def _get_other_cells(wing):
        node_a, node_b, node_c = None, None, None
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
            node_a = subset.pop()
            node_b = subset.pop()
            node_c = set(wing[1:]).difference({node_a, node_b})
            node_c = node_c.pop()
        return node_a, node_b, node_c

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
                break
        for node in nodes:
            if z in board[node]:
                impacted_cells = impacted_cells.intersection(ALL_NBRS[node])
        impacted_cells = {cell_id for cell_id in impacted_cells if len(board[cell_id]) > 1}
        return impacted_cells

    """
    def _get_chain(nodes, z, w=None):
        chain = defaultdict(set)
        for node in nodes:
            chain[node] = {(candidate, 'lime') for candidate in board[node] if candidate not in (z, w)}
            if z in board[node]:
                chain[node].add((z, 'cyan'))
            if w and w in board[node]:
                chain[node].add((w, 'moccasin'))
        return chain
    """

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
                    cell_a, cell_b, cell_c = _get_other_cells(wing)
                    if len(_get_cells_candidates(wing[1:], common=False)) == 4:
                        z = _get_cells_candidates(wing[1:])
                        if len(z) == 1:
                            z = z.pop()
                            if len(board[wing[0]]) == 4 or z not in board[wing[0]]:
                                impacted_cells = _get_impacted_cells(wing, z)
                                if impacted_cells:
                                    to_eliminate = {(z, cell_id) for cell_id in impacted_cells if z in board[cell_id]}
                                    if to_eliminate:
                                        w = board[cell_c].replace(z, '')
                                        solver_status.capture_baseline(board, window)
                                        if window:
                                            window.options_visible = window.options_visible.union(wing).union(
                                                impacted_cells)
                                        eliminate_options(solver_status, board, to_eliminate, window)
                                        kwargs["solver_tool"] = "wxyz_wing_type_1"
                                        kwargs["chain_d"] = _get_chain(board, (wing[0],), z, w)
                                        kwargs["chain_a"] = _get_chain(board, wing[1:], z, w)
                                        kwargs["eliminate"] = to_eliminate
                                        kwargs["impacted_cells"] = {a_cell for _, a_cell in to_eliminate}
                                        wxyz_wing.options_removed += len(to_eliminate)
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

        for wing in wings:
            for cell_id in wing[1:]:
                if len(set(ALL_NBRS[cell_id]).intersection(wing)) == 3 or len(board[cell_id]) != 2:
                    break
            else:
                cell_a, cell_b, cell_c = _get_other_cells(wing)
                if cell_a:
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
                                    to_eliminate = {(z, cell_id) for cell_id in impacted_cells if z in board[cell_id]}
                                    if to_eliminate:
                                        solver_status.capture_baseline(board, window)
                                        if window:
                                            window.options_visible = window.options_visible.union(wing).union(
                                                impacted_cells)
                                        eliminate_options(solver_status, board, to_eliminate, window)
                                        kwargs["solver_tool"] = "wxyz_wing_type_2"
                                        kwargs["chain_d"] = _get_chain(board, (wing[0],), z, w)
                                        kwargs["chain_a"] = _get_chain(board, wing[1:], z, w)
                                        kwargs["eliminate"] = to_eliminate
                                        kwargs["impacted_cells"] = {a_cell for _, a_cell in to_eliminate}
                                        wxyz_wing.options_removed += len(to_eliminate)
                                        wxyz_wing.clues += len(solver_status.naked_singles)
                                        # print(f'\t{kwargs["solver_tool"]}')
                                        return True
        return False

    def _type_3():
        """ Two wing cells (excluding wing base) belong to the same house (row, column, or box).
        Sum of the two cells candidates consists of three values and candidates of one cell make
        subset of the other call candidates. The third wing cell (excluding wing base) has two candidates
        and one of its candidates (called W) is different from the candidates of the other two cells.
        The second candidate (called Z) is also common to the first or second cell, or both.
        Base cell has two or more candidates and one of them is W. If the cell has only candidates,
        the second one cannot be Z.
        Rating: 240 (?)
        """
        for wing in wings:
            for cell_id in wing[1:]:
                if len(set(ALL_NBRS[cell_id]).intersection(wing)) == 3:
                    break
            else:
                cell_a, cell_b, cell_c = _get_other_cells(wing)
                if cell_a:
                    subset_candidates = set(''.join(board[cell_id] for cell_id in {cell_a, cell_b}))
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
                            impacted_cells = _get_impacted_cells(wing, z)
                            if impacted_cells:
                                to_eliminate = {(z, cell_id) for cell_id in impacted_cells if z in board[cell_id]}
                                if to_eliminate:
                                    solver_status.capture_baseline(board, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(wing).union(
                                            impacted_cells)
                                    eliminate_options(solver_status, board, to_eliminate, window)
                                    kwargs["solver_tool"] = "wxyz_wing_type_3"
                                    kwargs["chain_d"] = _get_chain(board, (wing[0],), z, w)
                                    kwargs["chain_a"] = _get_chain(board, wing[1:], z, w)
                                    kwargs["eliminate"] = to_eliminate
                                    kwargs["impacted_cells"] = {a_cell for _, a_cell in to_eliminate}
                                    wxyz_wing.options_removed += len(to_eliminate)
                                    wxyz_wing.clues += len(solver_status.naked_singles)
                                    # print(f'\t{kwargs["solver_tool"]}')
                                    return True
        return False

    def _type_4_5():
        """ Two wing cells do not belong to the same house (row, column, or box).
        One of the cells has two candidates and the other one has two or three candidates.
        There is one common candidate Z in both cells.
        The other two wing cells form base: together they have three different candidates excluding
        Z (Type 4) or four candidates (Type 5).
        Selecting any base candidate either forces one of the first two cells to take Z value or
        creates XY-Wing (Type 4) or XYZ-Wing (Type 5)
        Rating: 240 (?)
        """
        for wing in wings:
            base_cells = [wing[0], ]
            for cell_id in wing[1:]:
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
                    impacted_cells = _get_impacted_cells(wing, z)
                    if impacted_cells:
                        to_eliminate = {(z, cell_id) for cell_id in impacted_cells if z in board[cell_id]}
                        if to_eliminate:
                            base_candidates = set(''.join(board[cell_id] for cell_id in base_cells))
                            solver_status.capture_baseline(board, window)
                            if window:
                                window.options_visible = window.options_visible.union(wing).union(
                                    impacted_cells)
                            eliminate_options(solver_status, board, to_eliminate, window)
                            kwargs["solver_tool"] = "wxyz_wing_type_4" if len(base_candidates) == 3 else\
                                                    "wxyz_wing_type_5"
                            kwargs["chain_d"] = _get_chain(board, base_cells, z)
                            kwargs["chain_a"] = _get_chain(board, (cell_a, cell_b), z)
                            kwargs["eliminate"] = to_eliminate
                            kwargs["impacted_cells"] = {a_cell for _, a_cell in to_eliminate}
                            wxyz_wing.options_removed += len(to_eliminate)
                            wxyz_wing.clues += len(solver_status.naked_singles)
                            # print(f'\t{kwargs["solver_tool"]}')
                            return True
        return False

    kwargs = {}
    wings = _get_possible_wings()
    if _type_1() or _type_2() or _type_3() or _type_4_5():
        return kwargs
    return None


@get_stats
def w_wing(solver_status, board, window):
    """Remove candidates (options) using W-Wing technique
    http://hodoku.sourceforge.net/en/tech_wings.php#w
    Rating: 150
    """

    bi_value_cells = get_bi_value_cells(board)
    strong_links = get_strong_links(board)
    init_remaining_candidates(board, solver_status)
    for pair in bi_value_cells:
        if len(bi_value_cells[pair]) > 1:
            va, vb = pair
            w_constraint = None
            w_base = None
            for positions in combinations(bi_value_cells[pair], 2):
                for strong_link in strong_links[va]:
                    if not set(positions).intersection(strong_link):
                        sl_a = set(strong_link).intersection(ALL_NBRS[positions[0]])
                        sl_b = set(strong_link).intersection(ALL_NBRS[positions[1]])
                        if sl_a and sl_b and sl_a != sl_b:
                            w_base = strong_link
                            w_constraint = va
                            break
                if w_constraint:
                    break
                for strong_link in strong_links[vb]:
                    if not set(positions).intersection(strong_link):
                        sl_a = set(strong_link).intersection(ALL_NBRS[positions[0]])
                        sl_b = set(strong_link).intersection(ALL_NBRS[positions[1]])
                        if sl_a and sl_b and sl_a != sl_b:
                            w_base = strong_link
                            w_constraint = vb
                            break
                if w_constraint:
                    break
            else:
                continue
            assert w_constraint
            other_value = vb if w_constraint == va else va
            impacted_cells = set(ALL_NBRS[positions[0]]).intersection(ALL_NBRS[positions[1]])
            impacted_cells = {cell for cell in impacted_cells if len(board[cell]) > 1}
            to_eliminate = [(other_value, cell) for cell in impacted_cells if other_value in board[cell]]
            if to_eliminate:
                kwargs = {}
                solver_status.capture_baseline(board, window)
                if window:
                    window.options_visible = window.options_visible.union(impacted_cells).union(
                        {positions[0], positions[1]}).union(get_pair_house(w_base))
                eliminate_options(solver_status, board, to_eliminate, window)
                kwargs["solver_tool"] = "w_wing"
                kwargs["chain_a"] = _get_chain(board, positions[:2], other_value)
                kwargs["chain_d"] = _get_chain(board, w_base, other_value, w_constraint)
                kwargs["eliminate"] = to_eliminate
                kwargs["impacted_cells"] = {a_cell for _, a_cell in to_eliminate}
                w_wing.options_removed += len(to_eliminate)
                w_wing.clues += len(solver_status.naked_singles)
                # print('\tw_wing')
                return kwargs
    return {}


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
                                return True
        return False

    init_remaining_candidates(board, solver_status)
    kwargs = {}
    for opt in SUDOKU_VALUES_LIST:
        if _find_franken_x_wing(True, opt):
            return kwargs
        if _find_franken_x_wing(False, opt):
            return kwargs
    return kwargs
