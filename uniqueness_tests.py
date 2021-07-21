# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

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

    # 'bi_values' data structure:
    # {'xy': {(row, col, box), ...}}

    def _get_c_chain():
        nodes = sorted(list(rectangle))
        c_chain = dict()
        color_1 = 'yellow'
        color_2 = 'lime'
        for node in nodes:
            if len(board[node]) == 2:
                c_chain[node] = {(bi_value[0], color_1), (bi_value[1], color_2)}
                color_1 = 'lime' if color_1 == 'yellow' else 'yellow'
                color_2 = 'lime' if color_2 == 'yellow' else 'yellow'
        return c_chain

    def _get_rectangle():
        in_rows = list(rows)
        in_cols = list(cols)
        return {in_rows[0] * 9 + in_cols[0], in_rows[0] * 9 + in_cols[1],
                in_rows[1] * 9 + in_cols[0], in_rows[1] * 9 + in_cols[1]}

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

    def _get_c_chain(floor_a, floor_b, node_a, node_b, z_value, by_row):
        c_chain = dict()
        fa = floor_a[0] * 9 + floor_a[1] if by_row else floor_a[1] * 9 + floor_a[0]
        fb = floor_b[0] * 9 + floor_b[1] if by_row else floor_b[1] * 9 + floor_b[0]
        c_chain[fa] = set()
        c_chain[fb] = set()
        c_chain[node_a] = {(z_value, 'cyan')}
        c_chain[node_b] = {(z_value, 'cyan')}
        return c_chain

    def _find_xyz(x, y, cells):
        return {cell for cell in cells if len(board[cell]) == 3 and x in board[cell] and y in board[cell]}

    def _check_rectangles(by_row):
        cells_by_x = CELLS_IN_ROW if by_row else CELLS_IN_COL
        cells_by_y = CELLS_IN_COL if by_row else CELLS_IN_ROW

        for floor_x in range(9):
            bi_values.clear()
            for floor_y in range(9):
                cell = cells_by_x[floor_x][floor_y]
                if len(board[cell]) == 2:
                    bi_values[board[cell]].add((floor_x, floor_y, CELL_SQR[cell]))
            for bi_value, in_cells in bi_values.items():
                if len(in_cells) == 2:
                    floor_a = in_cells.pop()
                    floor_b = in_cells.pop()
                    ya_ids = _find_xyz(bi_value[0], bi_value[1], cells_by_y[floor_a[1]])
                    yb_ids = _find_xyz(bi_value[0], bi_value[1], cells_by_y[floor_b[1]])
                    if len(ya_ids) == 1 and len(yb_ids) == 1:
                        node_a = ya_ids.pop()
                        node_b = yb_ids.pop()
                        house_a = CELL_ROW[node_a] if by_row else CELL_COL[node_a]
                        house_b = CELL_ROW[node_b] if by_row else CELL_COL[node_b]
                        boxes = {floor_a[2], floor_b[2], CELL_SQR[node_a], CELL_SQR[node_b]}
                        if house_a == house_b and board[node_a] == board[node_b] and len(boxes) == 2:
                            z_candidate = board[node_a].replace(bi_value[0], '').replace(bi_value[1], '')
                            to_remove = set()
                            for cell in set(ALL_NBRS[node_a]).intersection(ALL_NBRS[node_b]):
                                if z_candidate in board[cell]:
                                    to_remove.add((z_candidate, cell))
                            if to_remove:
                                c_chain = _get_c_chain(floor_a, floor_b, node_a, node_b, z_candidate, by_row)
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




