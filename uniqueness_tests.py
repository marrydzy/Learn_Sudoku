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






