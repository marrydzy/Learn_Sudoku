# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

# 'bi_values' data structure:
# {'xy': {(row, col, box), ...}}


from itertools import combinations
from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import is_clue, init_options, remove_options, get_stats
from utils import get_pairs, get_house_pairs


@get_stats
def test_1(solver_status, board, window):
    """Remove candidates (options) using Unique Rectangle technique
    (see https://www.learn-sudoku.com/unique-rectangle.html)"""

    def _get_c_chain():
        c_chain = dict()
        color_1 = 'yellow'
        color_2 = 'lime'
        for node in rectangle:
            if len(board[node]) == 2:
                c_chain[node] = {(bi_value[0], color_1), (bi_value[1], color_2)}
                color_1 = 'lime' if color_1 == 'yellow' else 'yellow'
                color_2 = 'lime' if color_2 == 'yellow' else 'yellow'
        return c_chain

    def _get_rectangle():
        in_rows = list(rows)
        in_cols = list(cols)
        return [in_rows[0] * 9 + in_cols[0], in_rows[0] * 9 + in_cols[1],
                in_rows[1] * 9 + in_cols[1], in_rows[1] * 9 + in_cols[0]]

    init_options(board, solver_status)
    kwargs = {}
    bi_values = defaultdict(set)
    for cell in range(81):
        if len(board[cell]) == 2:
            bi_values[board[cell]].add((CELL_ROW[cell], CELL_COL[cell], CELL_SQR[cell]))

    for bi_value, positions in bi_values.items():
        if len(positions) > 2:
            for troika in combinations(positions, 3):
                rows = {position[0] for position in troika}
                cols = {position[1] for position in troika}
                boxes = {position[2] for position in troika}
                if len(rows) == 2 and len(cols) == 2 and len(boxes) == 2:
                    rectangle = _get_rectangle()
                    if all(bi_value[0] in board[corner] and bi_value[1] in board[corner] for corner in rectangle):
                        for corner in rectangle:
                            if len(board[corner]) > 2:
                                to_remove = {(candidate, corner) for candidate in bi_value}
                                c_chain = _get_c_chain()
                                solver_status.capture_baseline(board, window)
                                remove_options(solver_status, board, to_remove, window)
                                if window:
                                    window.options_visible = window.options_visible.union(rectangle)
                                kwargs["solver_tool"] = "unique_rectangles"
                                kwargs["c_chain"] = c_chain
                                kwargs["impacted_cells"] = {cell for _, cell in to_remove}
                                kwargs["remove"] = to_remove
                                return kwargs
    return None


@get_stats
def test_2(solver_status, board, window):
    """Remove candidates (options) using Unique Rectangle technique
    (see https://www.learn-sudoku.com/unique-rectangle.html)"""

    # 'bi_values' data structure:
    # {'xy': {(row, col, box), ...}}

    def _get_c_chain(floor_a, floor_b, ceiling_a, ceiling_b, bi_value, z_value, by_row):
        c_chain = defaultdict(set)
        color_1 = 'yellow'
        color_2 = 'lime'

        c_chain[ceiling_a] = {(z_value, 'cyan')}
        c_chain[ceiling_b] = {(z_value, 'cyan')}
        fa = floor_a[0] * 9 + floor_a[1] if by_row else floor_a[1] * 9 + floor_a[0]
        fb = floor_b[0] * 9 + floor_b[1] if by_row else floor_b[1] * 9 + floor_b[0]
        nodes = [fa, fb, ceiling_b, ceiling_a]
        for node in nodes:
            c_chain[node].add((bi_value[0], color_1))
            c_chain[node].add((bi_value[1], color_2))
            color_1 = 'lime' if color_1 == 'yellow' else 'yellow'
            color_2 = 'lime' if color_2 == 'yellow' else 'yellow'
        return c_chain

    def _find_xyz(x, y, cells, by_row):
        if by_row:
            return {CELL_ROW[cell] for cell in cells if len(board[cell]) == 3 and x in board[cell] and y in board[cell]}
        else:
            return {CELL_COL[cell] for cell in cells if len(board[cell]) == 3 and x in board[cell] and y in board[cell]}

    def _check_rectangles(by_row):
        cells_by_x = CELLS_IN_ROW if by_row else CELLS_IN_COL
        cells_by_y = CELLS_IN_COL if by_row else CELLS_IN_ROW

        for floor_id_x in range(9):
            bi_values.clear()
            for floor_id_y in range(9):
                cell = cells_by_x[floor_id_x][floor_id_y]
                if len(board[cell]) == 2:
                    bi_values[board[cell]].add((floor_id_x, floor_id_y, CELL_SQR[cell]))
            for bi_value, positions in bi_values.items():
                if len(positions) == 2:
                    floor_a = positions.pop()
                    floor_b = positions.pop()
                    xa_ids = _find_xyz(bi_value[0], bi_value[1], cells_by_y[floor_a[1]], by_row)
                    xb_ids = _find_xyz(bi_value[0], bi_value[1], cells_by_y[floor_b[1]], by_row)
                    x_ids = xa_ids.intersection(xb_ids)
                    for x_id in x_ids:
                        ceiling_a = x_id * 9 + floor_a[1] if by_row else floor_a[1] * 9 + x_id
                        ceiling_b = x_id * 9 + floor_b[1] if by_row else floor_b[1] * 9 + x_id
                        boxes = {floor_a[2], floor_b[2], CELL_SQR[ceiling_a], CELL_SQR[ceiling_b]}
                        if board[ceiling_a] == board[ceiling_b] and len(boxes) == 2:
                            z_candidate = board[ceiling_a].replace(bi_value[0], '').replace(bi_value[1], '')
                            to_remove = set()
                            for cell in set(ALL_NBRS[ceiling_a]).intersection(ALL_NBRS[ceiling_b]):
                                if z_candidate in board[cell]:
                                    to_remove.add((z_candidate, cell))
                            if to_remove:
                                c_chain = _get_c_chain(floor_a, floor_b, ceiling_a, ceiling_b,
                                                       bi_value, z_candidate, by_row)
                                solver_status.capture_baseline(board, window)
                                remove_options(solver_status, board, to_remove, window)
                                if window:
                                    window.options_visible = window.options_visible.union(c_chain.keys())
                                kwargs["solver_tool"] = "unique_rectangles"
                                kwargs["c_chain"] = c_chain
                                kwargs["impacted_cells"] = {cell for _, cell in to_remove}
                                kwargs["remove"] = to_remove
                                # print('\tBingo!')
                                return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    bi_values = defaultdict(set)
    if _check_rectangles(True) or _check_rectangles(False):
        return kwargs
    return None


@get_stats
def test_3(solver_status, board, window):
    """Remove candidates (options) using Unique Rectangle technique
    (see https://www.learn-sudoku.com/unique-rectangle.html)"""

    def _set_c_chain(floor_a, floor_b, ceiling_a, ceiling_b, bi_value, z_values, naked_subset, by_row):
        c_chain.clear()
        color_1 = 'yellow'
        color_2 = 'lime'

        c_chain[ceiling_a] = {(z_values[0], 'cyan')}
        c_chain[ceiling_b] = {(z_values[1], 'cyan')}
        for cell in naked_subset:
            for value in board[cell]:
                c_chain[cell].add((value, 'cyan'))
        fa = floor_a[0] * 9 + floor_a[1] if by_row else floor_a[1] * 9 + floor_a[0]
        fb = floor_b[0] * 9 + floor_b[1] if by_row else floor_b[1] * 9 + floor_b[0]
        nodes = [fa, fb, ceiling_b, ceiling_a]
        for node in nodes:
            c_chain[node].add((bi_value[0], color_1))
            c_chain[node].add((bi_value[1], color_2))
            color_1 = 'lime' if color_1 == 'yellow' else 'yellow'
            color_2 = 'lime' if color_2 == 'yellow' else 'yellow'

    def _find_xyz(x, y, cells, by_row):
        if by_row:
            return {CELL_ROW[cell] for cell in cells if len(board[cell]) == 3 and x in board[cell] and y in board[cell]}
        else:
            return {CELL_COL[cell] for cell in cells if len(board[cell]) == 3 and x in board[cell] and y in board[cell]}

    def _naked_pair(ceiling_a, ceiling_b, z_a, z_b):
        for cell in set(ALL_NBRS[ceiling_a]).intersection(ALL_NBRS[ceiling_b]):
            if len(board[cell]) == 2 and z_a in board[cell] and z_b in board[cell]:
                for node in set(ALL_NBRS[cell]).intersection(
                        ALL_NBRS[ceiling_a]).intersection(ALL_NBRS[ceiling_b]):
                    if z_a in board[node]:
                        to_remove.add((z_a, node))
                    if z_b in board[node]:
                        to_remove.add((z_b, node))
                if to_remove:
                    print('\tTest 3 - naked pair')
                    return [cell, ]
        return None

    def _naked_subset(n, ceiling_a, ceiling_b, bi_value, z_a, z_b, by_row):
        cells = {cell for cell in set(ALL_NBRS[ceiling_a]).intersection(ALL_NBRS[ceiling_b]) if len(board[cell]) > 1}
        nodes = {cell for cell in cells if len(board[cell]) <= n and (z_a in board[cell] or z_b in board[cell])
                 and not set(board[cell]).intersection(bi_value)}
        # print(f'\n\n{cells = }')
        # print(f'{nodes = } {bi_value = }')
        # to_remove.add((bi_value[0], ceiling_a))
        # return {45}
        houses = [nodes.intersection(
            CELLS_IN_ROW[CELL_ROW[ceiling_a]] if by_row else CELLS_IN_COL[CELL_COL[ceiling_a]])]
        if CELL_SQR[ceiling_a] == CELL_SQR[ceiling_b]:
            houses.append(nodes.intersection(CELLS_IN_SQR[CELL_SQR[ceiling_a]]))
        for house in houses:
            for subset in combinations(house, n-1):
                # print(f'\n{subset = }')
                values = set("".join(board[cell_id] for cell_id in subset)).union({z_a, z_b})
                # print(f'\n\n{subset = }, {values = }')
                if len(values) == n:
                    impacted_cells = cells
                    for cell in subset:
                        impacted_cells = impacted_cells.intersection(ALL_NBRS[cell])
                    for cell in impacted_cells:
                        for candidate in values.intersection(board[cell]):
                            to_remove.add((candidate, cell))
                if to_remove:
                    # print(f'\n{nodes = }, {subset = }')
                    # print(f'\tTest 3 - naked {n}')
                    # if n == 4:
                        # raise Exception
                    return subset
        return None

    def _check_rectangles(by_row):
        cells_by_x = CELLS_IN_ROW if by_row else CELLS_IN_COL
        cells_by_y = CELLS_IN_COL if by_row else CELLS_IN_ROW

        for floor_id_x in range(9):
            bi_values.clear()
            for floor_id_y in range(9):
                cell = cells_by_x[floor_id_x][floor_id_y]
                if len(board[cell]) == 2:
                    bi_values[board[cell]].add((floor_id_x, floor_id_y, CELL_SQR[cell]))
            for bi_value, positions in bi_values.items():
                if len(positions) == 2:
                    floor_a = positions.pop()
                    floor_b = positions.pop()
                    xa_ids = _find_xyz(bi_value[0], bi_value[1], cells_by_y[floor_a[1]], by_row)
                    xb_ids = _find_xyz(bi_value[0], bi_value[1], cells_by_y[floor_b[1]], by_row)
                    x_ids = xa_ids.intersection(xb_ids)
                    for x_id in x_ids:
                        ceiling_a = x_id * 9 + floor_a[1] if by_row else floor_a[1] * 9 + x_id
                        ceiling_b = x_id * 9 + floor_b[1] if by_row else floor_b[1] * 9 + x_id
                        boxes = {floor_a[2], floor_b[2], CELL_SQR[ceiling_a], CELL_SQR[ceiling_b]}
                        if len(boxes) == 2 and board[ceiling_a] != board[ceiling_b]:
                            z_a = board[ceiling_a].replace(bi_value[0], '').replace(bi_value[1], '')
                            z_b = board[ceiling_b].replace(bi_value[0], '').replace(bi_value[1], '')
                            # naked_subset = _naked_pair(ceiling_a, ceiling_b, z_a, z_b)
                            if not to_remove:
                                naked_subset = _naked_subset(2, ceiling_a, ceiling_b, bi_value, z_a, z_b, by_row)
                            if not to_remove:
                                naked_subset = _naked_subset(3, ceiling_a, ceiling_b, bi_value, z_a, z_b, by_row)
                            if not to_remove:
                                naked_subset = _naked_subset(4, ceiling_a, ceiling_b, bi_value, z_a, z_b, by_row)
                            if to_remove:
                                _set_c_chain(floor_a, floor_b, ceiling_a, ceiling_b, bi_value, (z_a, z_b),
                                             naked_subset, by_row)
                                solver_status.capture_baseline(board, window)
                                remove_options(solver_status, board, to_remove, window)
                                if window:
                                    window.options_visible = window.options_visible.union(c_chain.keys())
                                kwargs["solver_tool"] = "unique_rectangles"
                                kwargs["c_chain"] = c_chain
                                kwargs["impacted_cells"] = {cell for _, cell in to_remove}
                                kwargs["remove"] = to_remove
                                return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    bi_values = defaultdict(set)
    c_chain = defaultdict(set)
    to_remove = set()
    if _check_rectangles(True) or _check_rectangles(False):
        return kwargs
    return None



