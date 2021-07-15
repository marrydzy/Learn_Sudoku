# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from itertools import combinations
from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import is_clue, init_options, remove_options
from utils import get_pairs, get_house_pairs


def remote_pairs(solver_status, board, window):
    """ TODO """

    def _find_chain(pair):
        chain_cells = set(pairs_positions[pair])
        ends = [cell_id for cell_id in chain_cells if len(set(ALL_NBRS[cell_id]).intersection(chain_cells)) == 1]
        inner_nodes = [cell_id for cell_id in chain_cells if len(set(ALL_NBRS[cell_id]).intersection(chain_cells)) == 2]
        if len(ends) == 2 and ends[0] not in ALL_NBRS[ends[1]] and len(ends) + len(inner_nodes) == len(chain_cells):
            # print('\n')
            chain = [ends[0]]
            while inner_nodes:
                for node in inner_nodes:
                    if chain[-1] in set(ALL_NBRS[node]):
                        chain.append(node)
                        break
                if chain[-1] in inner_nodes:
                    inner_nodes.remove(chain[-1])
                elif len(chain) % 2 == 0:
                    return []
                else:
                    break
            chain.append(ends[1])
            return chain
        else:
            return []

    init_options(board, solver_status)
    pairs_positions = defaultdict(list)
    for cell in range(81):
        if len(board[cell]) == 2:
            pairs_positions[board[cell]].append(cell)
    pair_chains = [pair for pair in pairs_positions if
                   len(pairs_positions[pair]) > 3 and len(pairs_positions[pair]) % 2 == 0]
    for pair in pair_chains:
        chain = _find_chain(pair)
        if chain:
            impacted_cells = set(ALL_NBRS[chain[0]]).intersection(set(ALL_NBRS[chain[-1]]))
            to_remove = [(value, cell) for value in pair for cell in impacted_cells
                         if value in board[cell] and not is_clue(cell, board, solver_status)]
            if to_remove:
                solver_status.capture_baseline(board, window)
                if window:
                    window.options_visible = window.options_visible.union(impacted_cells)
                remove_options(solver_status, board, to_remove, window)
                kwargs = {
                    "solver_tool": "remote_pairs",
                    "chain": chain,
                    "remove": to_remove,
                    "impacted_cells": impacted_cells,
                }
                return kwargs

    return {}


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
                    boxes = {indx // 3 for indx in secondary_units}
                    for finned_indx, finned_values in finned.items():
                        if boxes == {indx // 3 for indx in secondary_units.union(finned_values)}:
                            in_primary_units = defaultdict(int)
                            for indx in secondary_units:
                                if indx in list(primary_units.values())[0]:
                                    in_primary_units[indx] += 1
                                if indx in list(primary_units.values())[1]:
                                    in_primary_units[indx] += 1
                                if indx in finned_values:
                                    in_primary_units[indx] += 1
                            if all((in_primary_units[indx] == 2 for indx in secondary_units)):
                                corners = [opt]
                                if by_row:
                                    corners.extend(
                                        [indx * 9 + unit for indx in primary_units for unit in primary_units[indx]])
                                    corners.extend([finned_indx * 9 + unit for unit in finned_values])
                                else:
                                    corners.extend(
                                        [unit * 9 + indx for indx in primary_units for unit in primary_units[indx]])
                                    corners.extend([unit * 9 + finned_indx for unit in finned_values])

                                fin_cells = [finned_indx * 9 + indx if by_row else indx * 9 + finned_indx
                                             for indx in finned_values.difference(secondary_units)]
                                impacted_cells = set(CELLS_IN_SQR[CELL_SQR[fin_cells[0]]]).difference(set(fin_cells))
                                secondary_cells = set()
                                for indx in secondary_units:
                                    secondary_cells = secondary_cells.union(
                                        set(CELLS_IN_COL[indx] if by_row else CELLS_IN_ROW[indx]))
                                impacted_cells = impacted_cells.intersection(secondary_cells)
                                for cell in corners[1:]:
                                    impacted_cells.discard(cell)

                                house = set(cells[list(primary_units.keys())[0]]).union(
                                            set(cells[list(primary_units.keys())[1]])).union(
                                            set(cells[finned_indx]))
                                to_remove = [(opt, cell) for cell in impacted_cells if opt in board[cell]]
                                if to_remove:
                                    solver_status.capture_baseline(board, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(set(house))
                                    remove_options(solver_status, board, to_remove, window)
                                    kwargs["solver_tool"] = "finned_swordfish"
                                    kwargs["singles"] = solver_status.naked_singles
                                    kwargs["nodes"] = corners
                                    kwargs["remove"] = to_remove
                                    kwargs["impacted_cells"] = impacted_cells
                                    kwargs["house"] = house
                                    return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    if _find_finned_swordfish(True):
        return kwargs
    if _find_finned_swordfish(False):
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


def empty_rectangle(solver_status, board, window):
    """ The relatively good description of Empty Rectangle strategy is
     available at Sudoku Coach page (http://www.taupierbw.be/SudokuCoach/SC_EmptyRectangle.shtml)
     - although it is not complete
     Rating: 120 - 140 """

    by_row_boxes = [[[3, 6], [4, 7], [5, 8]],
                    [[0, 6], [1, 7], [2, 8]],
                    [[0, 3], [1, 4], [2, 5]]]
    by_col_boxes = [[[1, 2], [4, 5], [7, 8]],
                    [[0, 2], [3, 5], [6, 8]],
                    [[0, 1], [3, 4], [6, 7]]]

    def _find_empty_rectangle(idx, by_row):
        cells_by_x = CELLS_IN_ROW if by_row else CELLS_IN_COL
        cells_by_y = CELLS_IN_COL if by_row else CELLS_IN_ROW
        cells = cells_by_x[idx]
        opts = ''.join(board[cell] for cell in cells if not is_clue(cell, board, solver_status))
        for val in SUDOKU_VALUES_LIST:
            if opts.count(val) == 2:
                idy = [j for j in range(9) if val in board[cells[j]]]
                if CELL_SQR[idy[0]] != CELL_SQR[idy[1]]:
                    for i in range(2):
                        for j in range(2):
                            box = by_row_boxes[idx//3][idy[i]//3][j] if by_row else by_col_boxes[idx//3][idy[i]//3][j]
                            central_line = (box // 3) * 3 + 1 if by_row else (box % 3) * 3 + 1
                            box_cells = set(CELLS_IN_SQR[box])
                            central_line_cells = set(cells_by_x[central_line]).intersection(box_cells)
                            cross_cells = box_cells.intersection(central_line_cells.union(set(cells_by_y[idy[i]])))
                            rect_corners = box_cells.difference(cross_cells)
                            corners_values = ''.join(board[cell] for cell in rect_corners)
                            if corners_values.count(val) == 0:
                                hole_cells = list(central_line_cells.difference(set(cells_by_y[idy[i]])))
                                if val in board[hole_cells[0]] or val in board[hole_cells[1]]:
                                    impacted_cell = cells_by_y[idy[(i + 1) % 2]][central_line]
                                    if val in board[impacted_cell]:
                                        to_remove = [(val, impacted_cell)]
                                        if to_remove:
                                            corners = set(cell for cell in cells_by_x[idx] if val in board[cell])
                                            if val in board[hole_cells[0]]:
                                                corners.add(hole_cells[0])
                                            if val in board[hole_cells[1]]:
                                                corners.add(hole_cells[1])
                                            corners = list(corners)
                                            corners.insert(0, val)
                                            house = set(cells).union(cross_cells)
                                            solver_status.capture_baseline(board, window)
                                            solver_status.capture_baseline(board, window)
                                            if window:
                                                window.options_visible = window.options_visible.union(house)
                                            remove_options(solver_status, board, to_remove, window)
                                            kwargs["solver_tool"] = "empty_rectangle"
                                            kwargs["house"] = house
                                            kwargs["impacted_cells"] = (impacted_cell,)
                                            kwargs["remove"] = [(val, impacted_cell)]
                                            kwargs["nodes"] = corners
                                            return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for indx in range(9):
        if _find_empty_rectangle(indx, True):
            return kwargs
        if _find_empty_rectangle(indx, False):
            return kwargs
    return kwargs
