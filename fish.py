# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS:
    X-Wing,
    swordfish
    jellyfish
    squirmbag
    finned_x_wings

    important data structures:
    c_chain:  {node: {(candidate, color), ...}, ...}
    n_values: {row: {col1, ...}, ...} if 'by_row',
              {column: {row1,...}, ...} otherwise
"""

from itertools import combinations
from collections import defaultdict

from utils import CELL_ROW, CELL_COL, CELL_SQR, CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_SQR, SUDOKU_VALUES_LIST
from utils import init_options, remove_options, get_pairs, get_stats, is_clue, get_n_values


def _basic_fish(solver_status, board, window, n):
    """ TODO """

    strategy_name = {2: "x_wings",
                     3: "swordfish",
                     4: "jellyfish",
                     5: "squirmbag"}

    def _get_corners(rows, columns):
        return [rows[0] * 9 + columns[0], rows[0] * 9 + columns[1],
                rows[1] * 9 + columns[0], rows[1] * 9 + columns[1]]

    def _get_c_chain(candidate, cells, primary_ids):
        nodes = {cell for idx in primary_ids for cell in cells[idx] if candidate in board[cell]}
        return {node: {(candidate, 'cyan')} for node in nodes}

    def _find_fish(by_row):
        for value in SUDOKU_VALUES_LIST:
            n_values = get_n_values(board, value, n, by_row)
            if len(n_values) >= n:
                primary_ids = [id_x for id_x in n_values]
                for x_ids in combinations(primary_ids, n):
                    secondary_ids = set(id_y for id_x in x_ids for id_y in n_values[id_x])
                    if len(secondary_ids) == n:
                        cells = CELLS_IN_COL if by_row else CELLS_IN_ROW
                        impacted_cells = {cell for id_y in secondary_ids for cell in cells[id_y]}
                        cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
                        houses = {cell for id_x in x_ids for cell in cells[id_x]}
                        impacted_cells = impacted_cells.difference(houses)
                        to_remove = {(value, cell) for cell in impacted_cells if value in board[cell]}
                        if to_remove:
                            solver_status.capture_baseline(board, window)
                            if window:
                                window.options_visible = window.options_visible.union(houses).union(impacted_cells)
                            remove_options(solver_status, board, to_remove, window)
                            if n == 2:
                                rows = sorted(list(x_ids if by_row else secondary_ids))
                                columns = sorted(list(secondary_ids if by_row else x_ids))
                                kwargs["x_wing"] = _get_corners(rows, columns)
                            kwargs["solver_tool"] = strategy_name[n]
                            kwargs["c_chain"] = _get_c_chain(value, cells, x_ids)
                            kwargs["remove"] = to_remove
                            kwargs["impacted_cells"] = {cell for _, cell in to_remove}
                            kwargs["house"] = houses
                            return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    if _find_fish(True):
        return kwargs
    if _find_fish(False):
        return kwargs
    return None


def _finned_fish(solver_status, board, window, n):
    """ TODO """

    def _get_c_chain(candidate, cells, primary_ids):
        nodes = {cell for idx in primary_ids for cell in cells[idx] if candidate in board[cell]}
        return {node: {(candidate, 'cyan')} for node in nodes}

    def _get_fins(n_values, x_ids):
        y_ids = [id_y for id_x in x_ids for id_y in n_values[id_x]]
        fins = defaultdict(set)
        for id_x in x_ids:
            if len(n_values[id_x]) > 2:
                for id_y in n_values[id_x]:
                    if y_ids.count(id_y) == 1:
                        box_y0 = (id_y // 3) * 3
                        box_ys = {box_y0, box_y0 + 1, box_y0 + 2}
                        if len(box_ys.intersection(n_values[id_x])) > 1:
                            fins[id_x].add(id_y)
        return fins

    def _get_strategy_name(n_values, x_ids, fin_x, fin_ys):
        strategy_name = {2: "finned_x_wings",
                         3: "finned_swordfish",
                         4: "finned_jellyfish",
                         5: "finned_squirmbag",
                         6: "sashimi_x_wing",
                         7: "sashimi_swordfish",
                         8: "sashimi_jellyfish",
                         9: "sashimi_squirmbag", }

        y_ids = {id_y for id_y in n_values[fin_x] if id_y not in fin_ys}
        method_id = n if len(y_ids) >= 2 else n + 4
        return strategy_name[method_id]

    def _get_fin_box(fin, by_row):
        return CELLS_IN_SQR[CELL_SQR[fin[0]*9 + fin[1] if by_row else fin[1]*9 + fin[0]]]

    def _find_finned_fish(by_row):
        for value in SUDOKU_VALUES_LIST:
            n_values = get_n_values(board, value, n+2, by_row)
            if len(n_values) >= n:
                primary_ids = [id_x for id_x in n_values]
                for x_ids in combinations(primary_ids, n):
                    secondary_ids = set(id_y for id_x in x_ids for id_y in n_values[id_x])
                    if len(secondary_ids) in (n+1, n+2):
                        fins = _get_fins(n_values, x_ids)
                        if len(fins) == 1:
                            fin_x = set(fins.keys()).pop()
                            fin_ys = list(fins[fin_x])
                            fin_box = _get_fin_box((fin_x, fin_ys[0]), by_row)
                            if len(secondary_ids) == n+1 and len(fin_ys) == 1 or \
                                    len(secondary_ids) == n+2 and len(fin_ys) == 2 and \
                                    _get_fin_box((fin_x, fin_ys[1]), by_row) == fin_box:
                                y_ids = secondary_ids.copy()
                                for y_id in fin_ys:
                                    y_ids.remove(y_id)
                                cells = CELLS_IN_COL if by_row else CELLS_IN_ROW
                                impacted_cells = {cell for id_y in y_ids for cell in cells[id_y]}
                                impacted_cells = impacted_cells.intersection(fin_box)
                                cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
                                houses = {cell for id_x in x_ids for cell in cells[id_x]}
                                impacted_cells = impacted_cells.difference(houses)
                                to_remove = {(value, cell) for cell in impacted_cells if value in board[cell]}
                                if to_remove:
                                    solver_status.capture_baseline(board, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(houses).union(impacted_cells)
                                    remove_options(solver_status, board, to_remove, window)
                                    c_chain = _get_c_chain(value, cells, x_ids)
                                    kwargs["solver_tool"] = _get_strategy_name(n_values, x_ids, fin_x, fin_ys)
                                    kwargs["c_chain"] = c_chain
                                    kwargs["remove"] = to_remove
                                    kwargs["impacted_cells"] = {cell for _, cell in to_remove}
                                    kwargs["house"] = houses

                                    # if kwargs["solver_tool"] == "sashimi_squirmbag":
                                    if n == 5:
                                        print(f'\t{kwargs["solver_tool"] = }')

                                    return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    if _find_finned_fish(True):
        return kwargs
    if _find_finned_fish(False):
        return kwargs
    return None


@get_stats
def x_wing(solver_status, board, window):
    """ One of the 'Basic Fish' techniques:
    see description e.g. at:
    https://www.sudopedia.org/wiki/X-Wing, or
    https://www.learn-sudoku.com/x-wing.html)
    Rating: 90 - 140
    """
    return _basic_fish(solver_status, board, window, 2)


@get_stats
def swordfish(solver_status, board, window):
    """ One of the 'Basic Fish' techniques:
     see description e.g. at:
     https://www.sudopedia.org/wiki/Swordfish
     Rating: 140 - 150
     """
    return _basic_fish(solver_status, board, window, 3)


@get_stats
def jellyfish(solver_status, board, window):
    """ One of the 'Basic Fish' techniques:
     see description e.g. at:
     https://www.sudopedia.org/wiki/Jellyfish
     Rating: 470
     """
    return _basic_fish(solver_status, board, window, 4)


@get_stats
def squirmbag(solver_status, board, window):
    """ TODO """
    ret = _basic_fish(solver_status, board, window, 5)
    if ret:
        # print('\tsquirmbag')
        pass
    return ret


@get_stats
def finned_x_wing(solver_status, board, window):
    """ The algorithm covers two of the 'Finned Fish' techniques:
     - Finned X-Wing (see description e.g. at:
       https://www.sudopedia.org/wiki/Finned_X-Wing), and
     - Sashimi X-Wing (Double Fin) (see description e.g. at:
       https://www.sudopedia.org/wiki/Sashimi_X-Wing)
       Sashimi X-Wing (Single Fin) is covered by Skyscraper.
    Rating: 130 (Finned X-Wing), 150 (Sashimi X-Wing)
    """
    return _finned_fish(solver_status, board, window, 2)


@get_stats
def finned_swordfish(solver_status, board, window):
    """ The algorithm covers two of the 'Finned Fish' techniques:
     - Finned Swordfish (see description e.g. at:
       https://www.sudopedia.org/wiki/Finned_Swordfish), and
     - Sashimi Swordfish (see description e.g. at:
       https://www.sudopedia.org/wiki/Sashimi_Swordfish)
    Rating: 200 (Finned Swordfish), 300 - 260 (Sashimi Swordfish)
    """
    return _finned_fish(solver_status, board, window, 3)


@get_stats
def finned_jellyfish(solver_status, board, window):
    """ The algorithm covers two of the 'Finned Fish' techniques:
     - Finned Jellyfish (see description e.g. at:
       https://www.sudopedia.org/wiki/Finned_Jellyfish), and
     - Sashimi Jellyfish (see description e.g. at:
       https://www.sudopedia.org/wiki/Sashimi_Jellyfish)
    Rating: 240 (Finned Swordfish), 250 (Sashimi Swordfish)
    """
    return _finned_fish(solver_status, board, window, 4)


def finned_squirmbag(solver_status, board, window):
    return _finned_fish(solver_status, board, window, 5)

