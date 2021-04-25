# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

import itertools
from collections import defaultdict

# from icecream import ic

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import is_clue, get_options, init_options, remove_options
# from utils import get_pairs


def open_singles(solver_status, board, window):
    """ 'Open Singles' technique (see: https://www.learn-sudoku.com/open-singles.html)
        The technique is applicable only in the initial phase of sudoku solving process when
        options in empty cells haven't been calculated yet.
    """

    def _set_missing_number(house):
        open_cells = [cell for cell in house if not is_clue(cell, board, window)]
        if len(open_cells) == 1:
            solver_status.capture_baseline(board, window)
            cell_id = open_cells.pop()
            missing_value = SUDOKU_VALUES_SET.copy() - set(
                ''.join(board[cell] for cell in house if is_clue(cell, board, window)))
            if len(missing_value) != 1:
                board[cell_id] = ''.join(missing_value)
                value_cells = defaultdict(list)
                for cell in house:
                    value_cells[board[cell]].append(cell)
                screwed = [cell_id]
                for value, cell in value_cells.items():
                    if len(cell) != 1:
                        screwed.extend(cell)
                window.critical_error = tuple(screwed)
                board[cell_id] = ''.join(value for value in missing_value)
            else:
                board[cell_id] = missing_value.pop()
                solver_status.clues_found.add(cell_id)
            kwargs["solver_tool"] = "open_singles"
            kwargs["new_clue"] = cell_id
            return True
        return False

    kwargs = {}
    if not solver_status.options_set:
        for i in range(9):
            if (_set_missing_number(CELLS_IN_ROW[i]) or _set_missing_number(CELLS_IN_COL[i]) or
                    _set_missing_number(CELLS_IN_SQR[i])):
                break
    return kwargs


def visual_elimination(solver_status, board, window):
    """ 'Visual Elimination' techniques (see: https://www.learn-sudoku.com/visual-elimination.html)
        The technique is applicable only in the initial phase of sudoku solving process when
        options in empty cells haven't been calculated yet.
        After finding a clue The function returns to the main solver loop to allow trying 'simpler'
        'open singles' method
    """
    def _check_zone(value, band):
        """ Look for lone singles in the band (vertical or horizontal stack of squares) """
        vertical = True if band < 3 else False
        band = band % 3
        cols_rows = CELLS_IN_COL if vertical else CELLS_IN_ROW
        with_clue = [cell for offset in range(3) for cell in cols_rows[3*band + offset] if board[cell] == value]
        if len(with_clue) == 2 and CELL_SQR[with_clue[0]] != CELL_SQR[with_clue[1]]:
            squares = [band + 3*offset if vertical else 3*band + offset for offset in range(3)]
            squares.remove(CELL_SQR[with_clue[0]])
            squares.remove(CELL_SQR[with_clue[1]])
            cells = set(CELLS_IN_SQR[squares[0]])
            if vertical:
                cells -= set(CELLS_IN_COL[CELL_COL[with_clue[0]]]).union(set(CELLS_IN_COL[CELL_COL[with_clue[1]]]))
            else:
                cells -= set(CELLS_IN_ROW[CELL_ROW[with_clue[0]]]).union(set(CELLS_IN_ROW[CELL_ROW[with_clue[1]]]))
            possible_clue_cells = [cell for cell in cells if not is_clue(cell, board, window)]
            clues = []
            greyed_out = []
            for cell in possible_clue_cells:
                if vertical:
                    other_clue = [cell_id for cell_id in CELLS_IN_ROW[CELL_ROW[cell]] if board[cell_id] == value]
                else:
                    other_clue = [cell_id for cell_id in CELLS_IN_COL[CELL_COL[cell]] if board[cell_id] == value]
                if other_clue:
                    with_clue.append(other_clue[0])
                    greyed_out.append(cell)
                else:
                    clues.append(cell)
            if len(clues) == 1:
                solver_status.capture_baseline(board, window)
                cell_id = clues[0]
                board[cell_id] = value
                solver_status.clues_found.add(cell_id)
                house = [cell for offset in range(3) for cell in cols_rows[3*band + offset]]
                kwargs["solver_tool"] = "visual_elimination"
                kwargs["new_clue"] = cell_id
                kwargs["greyed_out"] = greyed_out
                kwargs["house"] = house
                return True
        return False

    kwargs = {}
    if not solver_status.options_set:
        for digit in SUDOKU_VALUES_LIST:
            for zone in range(6):
                if _check_zone(digit, zone):
                    return kwargs
    return kwargs


def naked_singles(solver_status, board, window):
    """ 'Naked Singles' technique (see: https://www.learn-sudoku.com/lone-singles.html)
        In the initial phase of sudoku solving when options of all unsolved cells are not set yet,
        after finding a clue the function returns to the main solver loop to allow trying 'simpler'
        methods ('open singles' and then 'visual elimination').
        When options for all unsolved cells are already set the function continues solving naked singles until
        the 'naked_singles' list is empty (at this stage of sudoku solving it is the 'simplest' method)
    """
    kwargs = {}
    if solver_status.options_set:
        if not solver_status.naked_singles:
            return kwargs
        else:
            solver_status.capture_baseline(board, window)
            naked_single = solver_status.naked_singles.pop()
            clue = board[naked_single]  # TODO !!!!
            to_remove = [(clue, cell) for cell in ALL_NBRS[naked_single]
                         if not is_clue(cell, board, window) and clue in board[cell]]
            remove_options(solver_status, board, to_remove, window)
            kwargs["solver_tool"] = "naked_singles"
            kwargs["new_clue"] = naked_single
            kwargs["remove"] = to_remove
            solver_status.clues_found.add(naked_single)
            return kwargs
    else:
        for cell in range(81):
            if board[cell] == ".":
                cell_opts = get_options(cell, board, window)
                if len(cell_opts) == 1:
                    solver_status.capture_baseline(board, window)
                    board[cell] = cell_opts.pop()
                    kwargs["solver_tool"] = "naked_singles"
                    kwargs["new_clue"] = cell
                    solver_status.clues_found.add(cell)
                    return kwargs
        return kwargs


def hidden_singles(solver_status, board, window):
    """ 'Hidden Singles' technique (see: https://www.learn-sudoku.com/hidden-singles.html) """

    def _find_unique_positions(house):
        """ Find unique positions of missing clues within the house and 'solve' the cells """
        if solver_status.options_set:
            house_options = set(''.join(board[cell_id] for cell_id in house if len(board[cell_id]) > 1))
        else:
            house_options = SUDOKU_VALUES_SET.copy() - set(''.join([board[cell_id] for cell_id in house]))
        for option in house_options:
            in_cells = []
            greyed_out = []
            to_remove = []
            options_visible = window.options_visible if window else list()
            for cell in house:
                if board[cell] == ".":
                    cell_opts = get_options(cell, board, window)
                    if option in cell_opts:
                        in_cells.append(cell)
                    else:
                        greyed_out.append(cell)
                elif solver_status.options_set and len(board[cell]) > 1:
                    if option in board[cell]:
                        in_cells.append(cell)
                    elif cell not in options_visible:
                        greyed_out.append(cell)

            if len(in_cells) == 1:
                solver_status.capture_baseline(board, window)
                clue_id = in_cells[0]
                board[clue_id] = option
                solver_status.clues_found.add(clue_id)
                if solver_status.options_set:
                    to_remove = [(option, cell) for cell in ALL_NBRS[clue_id]
                                 if option in board[cell] and cell not in solver_status.clues_defined]
                    remove_options(solver_status, board, to_remove, window)
                kwargs["solver_tool"] = "hidden_singles"
                kwargs["new_clue"] = clue_id
                kwargs["house"] = house
                kwargs["greyed_out"] = greyed_out
                kwargs["remove"] = to_remove
                return True
        return False

    kwargs = {}
    for row in range(9):
        if _find_unique_positions(CELLS_IN_ROW[row]):
            return kwargs
    for col in range(9):
        if _find_unique_positions(CELLS_IN_COL[col]):
            return kwargs
    for sqr in range(9):
        if _find_unique_positions(CELLS_IN_SQR[sqr]):
            return kwargs
    return kwargs


def hidden_pair(solver_status, board, window):
    """A Hidden Pair is basically just a “buried” Naked Pair.
    It occurs when two pencil marks appear in exactly two cells within
    the same house (row, column, or block).
    This technique doesn't solve any cells; instead it reveals Naked Pairs
    by removing other candidates in the Naked Pair cells
    (see https://www.learn-sudoku.com/hidden-pairs.html)
    The method is called only when all unsolved cells have their options set
    The method exits after finding first Naked Pair
    """

    def _find_pairs(cells):
        values_dic = defaultdict(list)
        pairs_dic = defaultdict(list)

        for cell in cells:
            for value in board[cell]:
                values_dic[value].append(cell)
        for value, in_cells in values_dic.items():
            if len(in_cells) == 2:
                pairs_dic[tuple(in_cells)].append(value)

        for in_cells, values in pairs_dic.items():
            if len(values) == 2:
                pair = ''.join(values)
                other_options = [value for value in '123456789' if value not in pair]
                to_remove = \
                    [(option, cell) for option in other_options for cell in in_cells if option in board[cell]]
                if to_remove:
                    solver_status.capture_baseline(board, window)
                    remove_options(solver_status, board, to_remove, window)
                    kwargs["solver_tool"] = "hidden_pairs"
                    kwargs["claims"] = in_cells
                    kwargs["house"] = cells
                    kwargs["remove"] = to_remove
                    return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for i in range(9):
        if _find_pairs(CELLS_IN_ROW[i]):
            return kwargs
    for i in range(9):
        if _find_pairs(CELLS_IN_COL[i]):
            return kwargs
    for i in range(9):
        if _find_pairs(CELLS_IN_SQR[i]):
            return kwargs
    return kwargs


def hidden_triplet(solver_status, board, window):
    """When three given pencil marks appear in only three cells
    in any given row, column, or block, all other pencil marks may be removed
    from those cells.
    (see https://www.learn-sudoku.com/hidden-triplets.html)
    """

    def _find_triplets(cells):
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        options = set("".join(board[cell] for cell in unsolved))
        if len(unsolved) < 4 or len(options) < 4:
            return False

        options_dic = {value: {cell for cell in unsolved if value in board[cell]} for value in options}
        for triplet in itertools.combinations(options, 3):
            triplet_cells = set()
            for value in triplet:
                triplet_cells = triplet_cells.union(options_dic[value])
            if len(triplet_cells) == 3:
                remove_opts = set("".join(board[cell] for cell in triplet_cells)) - set(triplet)
                to_remove = [(value, cell) for value in remove_opts for cell in triplet_cells]
                if to_remove:
                    solver_status.capture_baseline(board, window)
                    remove_options(solver_status, board, to_remove, window)
                    kwargs["solver_tool"] = "hidden_triplets"
                    kwargs["claims"] = triplet_cells
                    kwargs["house"] = cells
                    kwargs["remove"] = to_remove
                    return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for i in range(9):
        if _find_triplets(CELLS_IN_ROW[i]):
            return kwargs
        if _find_triplets(CELLS_IN_COL[i]):
            return kwargs
        if _find_triplets(CELLS_IN_SQR[i]):
            return kwargs
    return kwargs


def hidden_quad(solver_status, board, window):
    """When three given pencil marks appear in only three cells
    in any given row, column, or block, all other pencil marks may be removed
    from those cells.
    (see https://www.learn-sudoku.com/hidden-triplets.html)
    """

    def _find_quad(cells):
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        options = set("".join(board[cell] for cell in unsolved))
        if len(unsolved) < 5 or len(options) < 5:
            return False

        options_dic = {value: {cell for cell in unsolved if value in board[cell]} for value in options}
        for quad in itertools.combinations(options, 4):
            quad_cells = set()
            for value in quad:
                quad_cells = quad_cells.union(options_dic[value])
            if len(quad_cells) == 4:
                remove_opts = set("".join(board[cell] for cell in quad_cells)) - set(quad)
                to_remove = [(value, cell) for value in remove_opts for cell in quad_cells]
                if to_remove:
                    solver_status.capture_baseline(board, window)
                    remove_options(solver_status, board, to_remove, window)
                    kwargs["solver_tool"] = "hidden_quads"
                    kwargs["claims"] = quad_cells
                    kwargs["house"] = cells
                    kwargs["remove"] = to_remove
                    return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for i in range(9):
        if _find_quad(CELLS_IN_ROW[i]):
            return kwargs
        if _find_quad(CELLS_IN_COL[i]):
            return kwargs
        if _find_quad(CELLS_IN_SQR[i]):
            return kwargs
    return kwargs


def naked_twins(solver_status, board, window):
    """ For each 'house' (row, column or square) find twin cells with two options
    and remove the values from the list of candidates (options) of the remaining cells
    (see https://www.learn-sudoku.com/naked-pairs.html)
    The method is called only when all unsolved cells have their options set
    The method exits after finding and 'fixing' such Naked Pair
    """

    def _find_pairs(cells):
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        pairs = defaultdict(list)
        for cell in unsolved:
            if len(board[cell]) == 2:
                pairs[board[cell]].append(cell)

        for values, in_cells in pairs.items():
            if len(in_cells) > 2:
                window.critical_error = tuple(in_cells)
            elif len(in_cells) == 2:
                unsolved.remove(in_cells[0])
                unsolved.remove(in_cells[1])
                to_remove = [(values[0], cell) for cell in unsolved if values[0] in board[cell]]
                to_remove.extend([(values[1], cell) for cell in unsolved if values[1] in board[cell]])
                if to_remove:
                    solver_status.capture_baseline(board, window)
                    remove_options(solver_status, board, to_remove, window)
                    kwargs["solver_tool"] = "naked_twins"
                    kwargs["claims"] = in_cells
                    kwargs["house"] = cells
                    kwargs["remove"] = to_remove
                    return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for i in range(9):
        if _find_pairs(CELLS_IN_ROW[i]):
            return kwargs
        if _find_pairs(CELLS_IN_COL[i]):
            return kwargs
        if _find_pairs(CELLS_IN_SQR[i]):
            return kwargs
    return kwargs


def naked_triplets(solver_status, board, window):
    """ For each 'house' (row, column or square) find triplets with total of three options
    and remove the values from the list of candidates (options) of the remaining cells
    (see https://www.learn-sudoku.com/naked-triplets.html)
    """

    def _find_triplets(cells):
        unsolved = {cell for cell in cells if len(board[cell]) > 1}
        if len(unsolved) > 3:
            for triplet in itertools.combinations(unsolved, 3):
                values = list(set("".join(board[cell_id] for cell_id in triplet)))
                if len(values) == 3:
                    other_cells = unsolved - set(triplet)
                    to_remove = [(values[idx], cell) for idx in range(3) for cell in other_cells
                                 if values[idx] in board[cell]]
                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "naked_triplets"
                        kwargs["claims"] = triplet
                        kwargs["house"] = cells
                        kwargs["remove"] = to_remove
                        return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for i in range(9):
        if _find_triplets(CELLS_IN_ROW[i]):
            return kwargs
        if _find_triplets(CELLS_IN_COL[i]):
            return kwargs
        if _find_triplets(CELLS_IN_SQR[i]):
            return kwargs
    return kwargs


def naked_quads(solver_status, board, window):
    """ For each 'house' (row, column or square) find quads with total of four options
    and remove the values from the list of candidates (options) of the remaining cells
    (see https://www.learn-sudoku.com/naked-triplets.html)
    """

    def _find_quad(cells):
        unsolved = {cell for cell in cells if len(board[cell]) > 1}
        if len(unsolved) > 4:
            for quad in itertools.combinations(unsolved, 4):
                values = list(set("".join(board[cell_id] for cell_id in quad)))
                if len(values) == 4:
                    other_cells = unsolved - set(quad)
                    to_remove = [(values[idx], cell) for idx in range(4) for cell in other_cells
                                 if values[idx] in board[cell]]
                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "naked_quads"
                        kwargs["claims"] = quad
                        kwargs["house"] = cells
                        kwargs["remove"] = to_remove
                        return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for i in range(9):
        if _find_quad(CELLS_IN_ROW[i]):
            return kwargs
        if _find_quad(CELLS_IN_COL[i]):
            return kwargs
        if _find_quad(CELLS_IN_SQR[i]):
            return kwargs
    return kwargs


def omissions(solver_status, board, window):
    """For rows and columns:
     - when pencil marks in a row or column are contained within a single square
       the pencil marks elsewhere in the square may be removed
    For blocks:
     - when pencil marks in a block are in one row or column, the pencil marks
       elsewhere in the row or the column can be removed
    (see: https://www.learn-sudoku.com/omission.html)
    """

    def _in_row_col(cells):
        options = SUDOKU_VALUES_SET - {board[cell] for cell in cells if len(board[cell]) == 1}
        if options:
            for value in options:
                unsolved = {cell for cell in cells if len(board[cell]) > 1}
                squares = {CELL_SQR[cell] for cell in unsolved if value in board[cell]}
                if len(squares) == 1:
                    impacted_cells = set(CELLS_IN_SQR[squares.pop()]) - set(cells)
                    to_remove = [(value, cell) for cell in impacted_cells if value in board[cell]]
                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "omissions"
                        kwargs["claims"] = [(to_remove[0][0], cell) for cell in cells]
                        kwargs["house"] = cells
                        kwargs["remove"] = to_remove
                        kwargs["impacted_cells"] = impacted_cells
                        return True
        return False

    def _in_block(cells):
        options = SUDOKU_VALUES_SET - {board[cell] for cell in cells if len(board[cell]) == 1}
        for value in options:
            unsolved = {cell for cell in cells if len(board[cell]) > 1}
            in_rows = set(CELL_ROW[cell] for cell in unsolved if value in board[cell])
            in_cols = set(CELL_COL[cell] for cell in unsolved if value in board[cell])
            if len(in_rows) == 1 or len(in_cols) == 1:
                impacted_cells = set()
                if len(in_rows) == 1:
                    impacted_cells = set(CELLS_IN_ROW[in_rows.pop()]) - set(cells)
                elif len(in_cols) == 1:
                    impacted_cells = set(CELLS_IN_COL[in_cols.pop()]) - set(cells)
                to_remove = [(value, cell) for cell in impacted_cells if value in board[cell]]
                if to_remove:
                    solver_status.capture_baseline(board, window)
                    remove_options(solver_status, board, to_remove, window)
                    kwargs["solver_tool"] = "omissions"
                    kwargs["claims"] = [(to_remove[0][0], cell) for cell in cells]
                    kwargs["house"] = cells
                    kwargs["remove"] = to_remove
                    kwargs["impacted_cells"] = impacted_cells
                    return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for i in range(9):
        if _in_row_col(CELLS_IN_ROW[i]):
            return kwargs
        if _in_row_col(CELLS_IN_COL[i]):
            return kwargs
        if _in_block(CELLS_IN_SQR[i]):
            return kwargs

    return kwargs
