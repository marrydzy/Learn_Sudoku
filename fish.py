# -*- coding: UTF-8 -*-

""" 'SUBSETS' CLASS OF SOLVING METHODS

    GLOBAL FUNCTIONS:
        x_wing() - 'X-Wing' sudoku solving strategy
        swordfish() - 'Swordfish' sudoku solving strategy
        jellyfish() - 'Jellyfish' sudoku solving strategy
        squirmbag() - 'Squirmbag' sudoku solving strategy
        finned_x_wing() - 'Finned X-Wing' sudoku solving strategy
        finned_swordfish() - 'Finned Swordfish' sudoku solving strategy
        finned_jellyfish() - 'Finned Jellyfish' sudoku solving strategy
        finned_squirmbag() - 'Finned Squirmbag' sudoku solving strategy

    LOCAL FUNCTIONS:
        _get_impacted_lines() - return unsolved cells in impacted lines (based on 'to_eliminate' data)
        _get_fin_box() - return set of cells of the 'finned' box
        _fish() - generic 'fish' solving strategy
        _finned_fish() - generic 'finned fish' solving strategy
        _sashimi_fish() - generic 'sashimi fish' solving strategy

    IMPORTANT DATA STRUCTURES:
        'chain_a':  {node: {(candidate, color), ...}, ...}
        'lines': {row: {col1, ...}, ...} if 'by_row', {column: {row1,...}, ...} otherwise
"""

from itertools import combinations
from collections import defaultdict, namedtuple

from utils import CELL_BOX, CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_BOX, SUDOKU_VALUES_LIST, CELL_COL, CELL_ROW
from utils import set_remaining_candidates, eliminate_options, get_stats, get_2_upto_n_candidates

Fin = namedtuple("Fin", ["x_id", "y_id"])


def _get_impacted_lines(to_eliminate, by_row, board):
    if by_row:
        return {cell for _, idx in to_eliminate for cell in CELLS_IN_COL[CELL_COL[idx]] if len(board[cell]) > 1}
    else:
        return {cell for _, idx in to_eliminate for cell in CELLS_IN_ROW[CELL_ROW[idx]] if len(board[cell]) > 1}


def _get_fin_box(fin, by_row):
    return set(CELLS_IN_BOX[CELL_BOX[fin.x_id * 9 + fin.y_id if by_row else fin.y_id * 9 + fin.x_id]])


def _fish(solver_status, board, window, n):
    """ Generic 'fish' technique """

    fish_strategies = {2: (x_wing, 100),
                       3: (swordfish, 140),
                       4: (jellyfish, 470),
                       5: (squirmbag, 470), }

    def _get_chain(candidate, cells, primary_ids):
        nodes = {cell for idx in primary_ids for cell in cells[idx] if candidate in board[cell]}
        return {node: {(candidate, 'cyan')} for node in nodes}

    def _find_fish(by_row):
        for value in SUDOKU_VALUES_LIST:
            lines = get_2_upto_n_candidates(board, value, n, by_row)
            if len(lines) >= n:
                for x_ids in combinations((id_x for id_x in lines), n):
                    y_ids = set(id_y for id_x in x_ids for id_y in lines[id_x])
                    if len(y_ids) == n:
                        cells = CELLS_IN_COL if by_row else CELLS_IN_ROW
                        impacted_cells = {cell for id_y in y_ids for cell in cells[id_y]}
                        cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
                        houses = {cell for id_x in x_ids for cell in cells[id_x]}
                        impacted_cells = impacted_cells.difference(houses)
                        to_eliminate = {(value, cell) for cell in impacted_cells if value in board[cell]}
                        if to_eliminate:
                            if window:
                                solver_status.capture_baseline(board, window)
                            kwargs["solver_tool"] = fish_strategies[n][0].__name__
                            eliminate_options(solver_status, board, to_eliminate, window)
                            fish_strategies[n][0].clues += len(solver_status.naked_singles)
                            fish_strategies[n][0].options_removed += len(to_eliminate)
                            if window:
                                impacted = _get_impacted_lines(to_eliminate, by_row, board)
                                window.options_visible = window.options_visible.union(houses).union(impacted_cells)
                                kwargs["chain_a"] = _get_chain(value, cells, x_ids)
                                kwargs["eliminate"] = to_eliminate
                                kwargs["house"] = impacted.union(houses)
                            return True
        return False

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    if _find_fish(True) or _find_fish(False):
        return kwargs
    return None


def _finned_fish(solver_status, board, window, n):
    """ Generic 'finned fish' technique """

    fish_strategies = {2: (finned_x_wing, 130),
                       3: (finned_swordfish, 200),
                       4: (finned_jellyfish, 240),
                       5: (finned_squirmbag, 470),
                       }

    def _get_fish_nodes(candidate, cells, x_ids):
        nodes = {cell for x_id in x_ids for cell in cells[x_id] if candidate in board[cell]}
        return {node: {(candidate, 'cyan')} for node in nodes}

    def _get_fins(lines, x_ids):
        """ return dictionary of 'fins' {x_id: {y_id, ...}} """
        y_ids = [id_y for id_x in x_ids for id_y in lines[id_x]]
        fins = defaultdict(set)
        for x_id in x_ids:
            if len(lines[x_id]) > 2:
                for y_id in lines[x_id]:
                    if y_ids.count(y_id) == 1:
                        box_y0 = (y_id // 3) * 3
                        box_ys = {box_y0, box_y0 + 1, box_y0 + 2}
                        if len(box_ys.intersection(lines[x_id])) > 1:
                            fins[x_id].add(y_id)
        return fins

    def _check_if_finned(lines, x_ids, y_ids):
        """ check if this is finned fish """

        for x_id in x_ids:                          # check X - lines
            line_nodes = {y_id for y_id in lines[x_id] if y_id in y_ids}
            if len(line_nodes) < 2:
                return False

        ys_counter = {y_id: 0 for y_id in y_ids}    # check Y - lines
        assert len(ys_counter) == n
        for x_id in x_ids:
            for y_id in ys_counter:
                if y_id in lines[x_id]:
                    ys_counter[y_id] += 1
        for y_id in ys_counter:
            if ys_counter[y_id] < 2:
                break
        else:
            return True
        return False

    def _find_finned_fish(by_row):
        """ TODO: Interestingly, as it is implemented the algorithm includes cells of
        other Y-lines if they cross the fin box (they should be only cells
        of the Y-line going through (x_id, y_id) node that is 'finned'.
        However, no issues were found that contradict such implementation of the method """
        for candidate in SUDOKU_VALUES_LIST:
            lines = get_2_upto_n_candidates(board, candidate, n+2, by_row)
            if len(lines) >= n:
                for x_ids in combinations(lines, n):
                    y_ids = set(y_id for x_id in x_ids for y_id in lines[x_id])
                    if len(y_ids) in (n+1, n+2) and len(fins := _get_fins(lines, x_ids)) == 1:
                        fin_x = set(fins).pop()
                        fin_ys = list(fins[fin_x])
                        fin_box = _get_fin_box(Fin(fin_x, fin_ys[0]), by_row)
                        if len(y_ids) == n+1 and len(fin_ys) == 1 or \
                                len(y_ids) == n+2 and len(fin_ys) == 2 and \
                                _get_fin_box(Fin(fin_x, fin_ys[1]), by_row) == fin_box:
                            y_ids = {y_id for y_id in y_ids if y_id not in fin_ys}
                            if _check_if_finned(lines, x_ids, y_ids):
                                cells = CELLS_IN_COL if by_row else CELLS_IN_ROW
                                impacted_cells = {cell for y_id in y_ids for cell in cells[y_id]}
                                impacted_cells = impacted_cells.intersection(fin_box)
                                cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
                                houses = {cell for x_id in x_ids for cell in cells[x_id]}
                                impacted_cells = impacted_cells.difference(houses)
                                to_eliminate = {(candidate, cell) for cell in impacted_cells
                                                if candidate in board[cell]}
                                if to_eliminate:
                                    if window:
                                        solver_status.capture_baseline(board, window)
                                        window.options_visible = window.options_visible.union(
                                            houses).union(impacted_cells)
                                        impacted = {cell for cell in impacted_cells if len(board[cell]) > 1}
                                        kwargs["house"] = impacted.union(houses)
                                    eliminate_options(solver_status, board, to_eliminate, window)
                                    fish_strategies[n][0].clues += len(solver_status.naked_singles)
                                    fish_strategies[n][0].options_removed += len(to_eliminate)
                                    kwargs["solver_tool"] = fish_strategies[n][0].__name__
                                    if window:
                                        kwargs["chain_a"] = _get_fish_nodes(candidate, cells, x_ids)
                                        kwargs["eliminate"] = to_eliminate
                                    return True
        return False

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    if _find_finned_fish(True) or _find_finned_fish(False):
        return kwargs
    return None


def _sashimi_fish(solver_status, board, window, n):
    """ Generic 'sashimi fish' technique """

    fish_strategies = {2: (sashimi_x_wing, 150),
                       3: (sashimi_swordfish, 240),
                       4: (sashimi_jellyfish, 280),
                       5: (sashimi_squirmbag, 470), }

    def _get_fish_nodes(candidate, x_ids, by_row):
        cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
        nodes = {cell for x_id in x_ids for cell in cells[x_id] if candidate in board[cell]}
        return {node: {(candidate, 'cyan')} for node in nodes}

    def _get_fins(lines, x_ids):
        """ return dictionary of 'fins' {x_id: {y_id, ...}} """
        y_ids = [y_id for x_id in x_ids for y_id in lines[x_id]]
        fins = defaultdict(set)
        for x_id in x_ids:
            for y_id in lines[x_id]:
                if y_ids.count(y_id) == 1:
                    box_y0 = (y_id // 3) * 3
                    other_box_ys = {box_y0, box_y0 + 1, box_y0 + 2}
                    other_box_ys.remove(y_id)
                    if other_box_ys.intersection(y_ids):
                        fins[x_id].add(y_id)
        return fins

    def _check_if_sashimi(lines, x_ids, y_ids):
        """ check if this is sashimi fish, not finned """
        xs_counter = {y_id: 0 for y_id in y_ids}
        for x_id in x_ids:
            line = lines[x_id]
            for y_id in xs_counter:
                if y_id in line:
                    xs_counter[y_id] += 1
        for y_id in xs_counter:
            if xs_counter[y_id] != 2:
                break
        else:
            return False
        return True

    def _find_sashimi_fish(by_row):
        for candidate in SUDOKU_VALUES_LIST:
            lines = get_2_upto_n_candidates(board, candidate, n+1, by_row)
            if len(lines) >= n:
                for x_ids in combinations(lines, n):
                    cells = CELLS_IN_ROW if by_row else CELLS_IN_COL
                    houses = {cell for x_id in x_ids for cell in cells[x_id]}
                    all_y_ids = set(idy for idx in x_ids for idy in lines[idx])
                    if len(all_y_ids) in (n, n+1):
                        if fins := _get_fins(lines, x_ids):
                            impacted_cells = set()
                            for fin_x in fins:
                                fin_ys = list(fins[fin_x])
                                fin_box = _get_fin_box(Fin(fin_x, fin_ys[0]), by_row)
                                if len(fin_ys) == 1 or len(fin_ys) == 2 and \
                                        _get_fin_box(Fin(fin_x, fin_ys[1]), by_row) == fin_box:
                                    y_ids = {y_id for y_id in all_y_ids if y_id not in fin_ys}
                                    if _check_if_sashimi(lines, x_ids, y_ids):
                                        cells = CELLS_IN_COL if by_row else CELLS_IN_ROW
                                        for y_id in y_ids:
                                            if fin_box.intersection(cells[y_id]):
                                                impacted_cells = impacted_cells.union(fin_box.intersection(cells[y_id]))
                                        impacted_cells = impacted_cells.difference(houses)
                            to_eliminate = {(candidate, cell) for cell in impacted_cells if candidate in board[cell]}
                            if to_eliminate:
                                if window:
                                    solver_status.capture_baseline(board, window)
                                    impacted = {cell for cell in impacted_cells if len(board[cell]) > 1}
                                    window.options_visible = window.options_visible.union(houses).union(impacted)
                                    kwargs["house"] = impacted.union(houses)
                                eliminate_options(solver_status, board, to_eliminate, window)
                                fish_strategies[n][0].clues += len(solver_status.naked_singles)
                                fish_strategies[n][0].options_removed += len(to_eliminate)
                                kwargs["solver_tool"] = fish_strategies[n][0].__name__
                                if window:
                                    kwargs["chain_a"] = _get_fish_nodes(candidate, x_ids, by_row)
                                    kwargs["eliminate"] = to_eliminate
                                return True
        return False

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    if _find_sashimi_fish(True) or _find_sashimi_fish(False):
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
    return _fish(solver_status, board, window, 2)


@get_stats
def swordfish(solver_status, board, window):
    """ One of the 'Basic Fish' techniques:
     see description e.g. at:
     https://www.sudopedia.org/wiki/Swordfish
     Rating: 140 - 150
     """
    return _fish(solver_status, board, window, 3)


@get_stats
def jellyfish(solver_status, board, window):
    """ One of the 'Basic Fish' techniques:
     see description e.g. at:
     https://www.sudopedia.org/wiki/Jellyfish
     Rating: 470
     """
    return _fish(solver_status, board, window, 4)


@get_stats
def squirmbag(solver_status, board, window):
    """ One of the 'Basic Fish' techniques:
     see description e.g. at:
     https://www.sudoku9981.com/sudoku-solving/squirmbag.php
     Rating: 470
     """
    return _fish(solver_status, board, window, 5)


@get_stats
def finned_x_wing(solver_status, board, window):
    """ The algorithm covers 'Finned X-Wing' technique:
     - see description e.g. at:
       https://www.sudopedia.org/wiki/Finned_X-Wing)
    Rating: 130
    """
    return _finned_fish(solver_status, board, window, 2)


@get_stats
def finned_swordfish(solver_status, board, window):
    """ The algorithm covers 'Finned Swordfish' technique:
     - see description e.g. at:
       https://www.sudopedia.org/wiki/Finned_Swordfish
    Rating: 200
    """
    return _finned_fish(solver_status, board, window, 3)


@get_stats
def finned_jellyfish(solver_status, board, window):
    """ The algorithm covers 'Finned Jellyfish' technique:
     - see description e.g. at:
       https://www.sudopedia.org/wiki/Finned_Jellyfish
    Rating: 240-250
    """
    return _finned_fish(solver_status, board, window, 4)


@get_stats
def finned_squirmbag(solver_status, board, window):
    """ The algorithm 'Finned Squirmbag' technique:
    Rating: 470
    """
    return _finned_fish(solver_status, board, window, 5)


@get_stats
def sashimi_x_wing(solver_status, board, window):
    """ The algorithm covers 'Sashimi X-Wing' technique:
     - see description e.g. at:
       https://www.sudopedia.org/wiki/Sashimi_X-Wing)
       Sashimi X-Wing (Single Fin) is identical with 'Skyscraper' technique.
    Rating: 150
    """
    return _sashimi_fish(solver_status, board, window, 2)


@get_stats
def sashimi_swordfish(solver_status, board, window):
    """ The algorithm covers 'Sashimi Swordfish' technique:
     - see description e.g. at:
       https://www.sudopedia.org/wiki/Sashimi_Swordfish
    Rating: 240
    """
    return _sashimi_fish(solver_status, board, window, 3)


@get_stats
def sashimi_jellyfish(solver_status, board, window):
    """ The algorithm covers Sashimi Jellyfish' technique:
     - see description e.g. at:
       https://www.sudopedia.org/wiki/Sashimi_Jellyfish
    Rating: 300-260
    """
    return _sashimi_fish(solver_status, board, window, 4)


@get_stats
def sashimi_squirmbag(solver_status, board, window):
    """ The algorithm covers 'Sashimi Squirmbag' technique:
    Rating: 470
    """
    return _sashimi_fish(solver_status, board, window, 5)
