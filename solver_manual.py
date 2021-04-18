# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

import itertools
from collections import defaultdict

# from icecream import ic

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import is_clue, is_solved, get_options, init_options, set_cell_options, set_neighbours_options
from utils import get_pairs


class SolverStatus:
    """ class to store data needed for recovering of puzzle
    status prior to applying a method """
    def __init__(self):
        self.options_set = False
        self.naked_singles = set()
        self.naked_singles_baseline = set()
        self.clues_found_baseline = []
        self.options_visible_baseline = set()
        self.conflicted_cells = []

    def capture_baseline(self, board, window):
        if window and window.show_solution_steps and not window.animate:
            window.set_current_board(board)
            self.naked_singles_baseline = self.naked_singles.copy()
            self.clues_found_baseline = window.clues_found.copy()
            self.options_visible_baseline = window.options_visible.copy()

    def restore_baseline(self, board, window):
        if window:
            self.naked_singles = self.naked_singles_baseline.copy()
            window.clues_found = self.clues_found_baseline.copy()
            window.options_visible = self.options_visible_baseline.copy()
            for cell_id in range(81):
                board[cell_id] = window.input_board[cell_id]

    def reset(self, board, window):
        self.options_set = False
        self.naked_singles.clear()
        self.naked_singles_baseline.clear()
        self.clues_found_baseline.clear()
        self.options_visible_baseline.clear()
        if window:
            for cell_id in range(81):
                if cell_id not in window.clues_defined:
                    board[cell_id] = "."
            window.set_current_board(board)


solver_status = SolverStatus()


def _remove_options(board, to_remove, window):
    """ utility function: removes options as per 'to_remove' list """
    for option, cell in to_remove:
        board[cell] = board[cell].replace(option, "")
        if not board[cell]:
            window.critical_error = (cell, )
        elif len(board[cell]) == 1:
            solver_status.naked_singles.add(cell)


def _the_same_as_clue_found(board, window, options_set):
    """ Entered key is the same as clicked cell value """
    cell_id, value, as_clue = window.clue_entered
    window.clues_found.remove(cell_id)
    if as_clue:
        if options_set:
            set_cell_options(cell_id, board, window, solver_status)
        else:
            board[cell_id] = "."
    else:
        window.options_visible.add(cell_id)
        solver_status.naked_singles.add(cell_id)
    if options_set:
        set_neighbours_options(cell_id, board, window, solver_status)


def _other_than_clue_found(board, window, options_set):
    """ Entered key other than clicked cell value """
    cell_id, value, as_clue = window.clue_entered
    if cell_id in solver_status.naked_singles:
        solver_status.naked_singles.remove(cell_id)
    board[cell_id] = value
    if as_clue:
        window.clues_found.add(cell_id)
    else:
        window.clues_found.remove(cell_id)
        solver_status.naked_singles.add(cell_id)
        window.options_visible.add(cell_id)
    if options_set:
        set_neighbours_options(cell_id, board, window, solver_status)


def _as_clue_and_undefined(board, window, options_set):
    """ Entering clue in undefined cell """
    cell_id, value, as_clue = window.clue_entered
    if cell_id in window.options_visible:
        window.options_visible.remove(cell_id)
    if cell_id in solver_status.naked_singles:
        solver_status.naked_singles.remove(cell_id)
    board[cell_id] = value
    window.clues_found.add(cell_id)
    if options_set:
        set_neighbours_options(cell_id, board, window, solver_status)


def _as_opt_and_undefined(board, window):
    """ Entering an option in undefined cell """
    cell_id, value, as_clue = window.clue_entered
    if cell_id in window.options_visible:
        if cell_id in solver_status.naked_singles:
            solver_status.naked_singles.remove(cell_id)
        if value in board[cell_id]:
            board[cell_id] = board[cell_id].replace(value, "")
            if len(board[cell_id]) == 0:
                set_cell_options(cell_id, board, window, solver_status)
                window.options_visible.remove(cell_id)
            elif len(board[cell_id]) == 1:
                solver_status.naked_singles.add(cell_id)
        else:
            board[cell_id] += value
    else:
        board[cell_id] = value
        window.options_visible.add(cell_id)
        solver_status.naked_singles.add(cell_id)


def _check_board_integrity(board, window):
    """ Check integrity of the current board:
     - check for conflicted cells in each row, column and box
     - if solved board is defined, check entered values (clues or options) if correct
    """

    def _check_house(cells):
        values_dict = defaultdict(list)
        for cell in cells:
            if is_clue(cell, board, window):
                values_dict[board[cell]].append(cell)
        for value, in_cells in values_dict.items():
            if len(in_cells) > 1:
                solver_status.conflicted_cells.extend(in_cells)

    solver_status.conflicted_cells.clear()
    for i in range(9):
        _check_house(CELLS_IN_ROW[i])
        _check_house(CELLS_IN_COL[i])
        _check_house(CELLS_IN_SQR[i])
    solver_status.conflicted_cells = list(set(solver_status.conflicted_cells))

    if window.solved_board:
        window.wrong_values.clear()
        for cell_id in range(81):
            if cell_id not in window.clues_defined:
                if cell_id in window.clues_found:
                    if board[cell_id] != window.solved_board[cell_id]:
                        window.wrong_values.add(cell_id)
                elif cell_id in window.options_visible:
                    if window.solved_board[cell_id] not in set(board[cell_id]):
                        window.wrong_values.add(cell_id)


def _set_manually(board, window):
    """ Interactively take entered values """
    kwargs = {}
    if window and window.clue_entered[0] is not None:
        solver_status.capture_baseline(board, window)
        cell_id, value, as_clue = window.clue_entered
        if cell_id in window.clues_found:
            if board[cell_id] == value:
                _the_same_as_clue_found(board, window, solver_status.options_set)
            else:
                _other_than_clue_found(board, window, solver_status.options_set)
        else:
            if as_clue:
                _as_clue_and_undefined(board, window, solver_status.options_set)
            else:
                _as_opt_and_undefined(board, window)
        _check_board_integrity(board, window)
        window.clue_entered = (None, None, None)
        cell_house = ALL_NBRS[solver_status.conflicted_cells[-1]] if solver_status.conflicted_cells else list()
        kwargs = {"solver_tool": "plain_board",
                  "wrong_values": window.wrong_values,
                  "conflicted_cells": solver_status.conflicted_cells,
                  "cell_house": cell_house,
                  }
    if is_solved(board, window):
        kwargs["solver_tool"] = "end_of_game"
    return kwargs


def _open_singles(board, window):
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
                if window:
                    window.clues_found.add(cell_id)
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


def _visual_elimination(board, window):
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
                if window:
                    window.clues_found.add(cell_id)
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


def _naked_singles(board, window):
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
            _remove_options(board, to_remove, window)
            kwargs["solver_tool"] = "naked_singles"
            kwargs["new_clue"] = naked_single
            kwargs["remove"] = to_remove
            if window:
                window.clues_found.add(naked_single)
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
                    if window:
                        window.clues_found.add(cell)
                    return kwargs
        return kwargs


def _hidden_singles(board, window):
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
                if window:
                    window.clues_found.add(clue_id)
                if solver_status.options_set:
                    to_remove = [(option, cell) for cell in ALL_NBRS[clue_id] if option in board[cell]]
                    _remove_options(board, to_remove, window)
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


def _hidden_pair(board, window):
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
                    _remove_options(board, to_remove, window)
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


def _hidden_triplet(board, window):
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
                    _remove_options(board, to_remove, window)
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


def _hidden_quad(board, window):
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
                    _remove_options(board, to_remove, window)
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


def _naked_twins(board, window):
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
                    _remove_options(board, to_remove, window)
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


def _naked_triplets(board, window):
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
                        _remove_options(board, to_remove, window)
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


def _naked_quads(board, window):
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
                        _remove_options(board, to_remove, window)
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


def _omissions(board, window):
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
                        _remove_options(board, to_remove, window)
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
                    _remove_options(board, to_remove, window)
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


def _y_wings(board, window):
    """Remove candidates (options) using XY Wing technique
    (see https://www.learn-sudoku.com/xy-wing.html)"""

    def _find_wings(cell_id):
        a_value, b_value = board[cell_id]
        corners_ax = defaultdict(list)
        corners_bx = defaultdict(list)
        for nbr_cell in ALL_NBRS[cell_id]:
            if len(board[nbr_cell]) == 2:
                if a_value in board[nbr_cell]:
                    x_value = board[nbr_cell].replace(a_value, "")
                    corners_ax[x_value].append(nbr_cell)
                elif b_value in board[nbr_cell]:
                    x_value = board[nbr_cell].replace(b_value, "")
                    corners_bx[x_value].append(nbr_cell)
        wings = [(x_value, cell_id, corner_ax, corner_bx)
                 for x_value in set(corners_ax) & set(corners_bx)
                 for corner_ax in corners_ax[x_value]
                 for corner_bx in corners_bx[x_value]]
        return wings

    def _reduce_xs(wings):
        for wing in wings:
            to_remove = []
            for cell_id in set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]]):
                if wing[0] in board[cell_id]:
                    to_remove.append((wing[0], cell_id))
            if to_remove:
                solver_status.capture_baseline(board, window)
                _remove_options(board, to_remove, window)
                kwargs["solver_tool"] = "y_wings"
                kwargs["y_wing"] = wing
                kwargs["remove"] = to_remove
                kwargs["impacted_cells"] = set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]])
                """
                if window:
                    if window.draw_board(board, "y_wings", y_wing=wing, remove=to_remove,
                                         impacted_cells=set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]])):
                        pass
                    else:
                        solver_status.restore_baseline(board, window)
                """
                return True
        return False

    init_options(board, window, solver_status)
    kwargs = {}
    for cell in range(81):
        if len(board[cell]) == 2 and _reduce_xs(_find_wings(cell)):
            return kwargs
    return kwargs


def _unique_rectangles(board, window):
    """Remove candidates (options) using Unique Rectangle technique
    (see https://www.learn-sudoku.com/unique-rectangle.html)"""

    # 'pairs' data structure:
    # {'xy': [(row, col, blk), ...]}

    # Finding unique rectangles:
    #  - a pair is in at least three cells and the pair values are in options of the fourth one
    #  - the pair is in exactly two rows, to columns and two blocks

    def _reduce_rectangle(pair, corners):
        if all(board[corner] == pair for corner in corners):
            return False
        to_remove = []
        for corner in corners:
            if board[corner] != pair:
                subset = [cell for cell in rect if len(board[cell]) == 2]
                if pair[0] in board[corner]:
                    to_remove.append((pair[0], corner))
                if pair[1] in board[corner]:
                    to_remove.append((pair[1], corner))
                if to_remove:
                    solver_status.capture_baseline(board, window)
                    _remove_options(board, to_remove, window)
                    if window:
                        window.options_visible = window.options_visible.union(set(corners))
                    kwargs["solver_tool"] = "unique_rectangles"
                    kwargs["rectangle"] = rect
                    kwargs["remove"] = to_remove
                    kwargs["subset"] = subset
                    return True
        return False

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


def _swordfish(board, window):
    """Remove candidates (options) using Swordfish technique
    (see https://www.learn-sudoku.com/x-wing.html)
    """

    def _find_swordfish(by_row):
        pairs_dict = get_pairs(board, by_row)
        # 'primary' direction: rows for 'by_row' direction, columns otherwise
        # 'secondary' direction: columns for 'by_row' direction, rows otherwise
        value_positions = defaultdict(list)
        for secondary_idxs, pairs in pairs_dict.items():
            for value, primary_idxs in pairs.items():
                if len(primary_idxs) == 1:
                    value_positions[value].append((primary_idxs[0], secondary_idxs[0], secondary_idxs[1]))
        for value, positions in value_positions.items():
            if len(positions) == 3:
                primary_idxs = []
                secondary_idxs = []
                house = []
                for position in positions:
                    primary_idxs.append(position[0])
                    secondary_idxs.append(position[1])
                    secondary_idxs.append(position[2])
                    house.extend(CELLS_IN_ROW[position[0]] if by_row else CELLS_IN_COL[position[0]])
                in_2_places = (secondary_idxs.count(index) == 2 for index in set(secondary_idxs))
                if all(in_2_places):
                    to_remove = []
                    sword = [value, ]
                    in_cells = set()    # TODO - change the name
                    for position in positions:
                        if by_row:
                            sword.append(position[0] * 9 + position[1])
                            sword.append(position[0] * 9 + position[2])
                            in_cells = in_cells.union(set(CELLS_IN_COL[position[1]]))
                            in_cells = in_cells.union(set(CELLS_IN_COL[position[2]]))
                        else:
                            sword.append(position[1] * 9 + position[0])
                            sword.append(position[2] * 9 + position[0])
                            in_cells = in_cells.union(set(CELLS_IN_ROW[position[1]]))
                            in_cells = in_cells.union(set(CELLS_IN_ROW[position[2]]))
                    secondary_idxs = set(secondary_idxs)
                    for index in secondary_idxs:
                        if by_row:
                            other_cells = [CELLS_IN_COL[index][row] for row in range(9)
                                           if len(board[CELLS_IN_COL[index][row]]) > 1 and row not in primary_idxs]
                        else:
                            other_cells = [CELLS_IN_ROW[index][col] for col in range(9)
                                           if len(board[CELLS_IN_ROW[index][col]]) > 1 and col not in primary_idxs]
                        to_remove.extend([(value, cell) for cell in other_cells if value in board[cell]])

                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        if window:
                            window.options_visible = window.options_visible.union(set(house))
                        _remove_options(board, to_remove, window)
                        kwargs["solver_tool"] = "swordfish"
                        kwargs["singles"] = solver_status.naked_singles
                        kwargs["sword"] = sword
                        kwargs["remove"] = to_remove
                        kwargs["impacted_cells"] = in_cells
                        kwargs["house"] = house
                        return True
        return False

    kwargs = {}
    if _find_swordfish(True):
        return kwargs
    if _find_swordfish(False):
        return kwargs
    return kwargs


def _x_wings(board, window):
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
                        _remove_options(board, to_remove, window)
                        kwargs["solver_tool"] = "x_wings"
                        kwargs["singles"] = solver_status.naked_singles
                        kwargs["x_wing"] = corners
                        kwargs["subset"] = [value]
                        kwargs["remove"] = to_remove
                        kwargs["impacted_cells"] = house
                        return True
        return False

    kwargs = {}
    if _find_x_wing(True):
        return kwargs
    if _find_x_wing(False):
        return kwargs
    return kwargs


def manual_solver(board, window):
    """ Main solver loop:
     - The algorithm draws current board and waits until a predefined event happens
     - Each '_method' function returns True if the board is updated, False otherwise
     - Interactive vs. step-wise execution is controlled by 'window.calculate_next_clue' parameter """

    solver_status.reset(board, window)
    kwargs = {"solver_tool": "plain_board"}
    while True:
        if window:
            window.draw_board(board, **kwargs)
            kwargs = _set_manually(board, window)
            if kwargs:
                continue
            if not window.calculate_next_clue:
                continue
            elif window.show_solution_steps:
                window.calculate_next_clue = False
        kwargs = _open_singles(board, window)
        if kwargs:
            continue
        kwargs = _visual_elimination(board, window)
        if kwargs:
            continue
        kwargs = _naked_singles(board, window)
        if kwargs:
            continue
        kwargs = _hidden_singles(board, window)
        if kwargs:
            continue
        kwargs = _naked_twins(board, window)
        if kwargs:
            continue
        kwargs = _hidden_pair(board, window)
        if kwargs:
            continue
        kwargs = _naked_triplets(board, window)
        if kwargs:
            continue
        kwargs = _hidden_triplet(board, window)
        if kwargs:
            continue
        kwargs = _naked_quads(board, window)
        if kwargs:
            continue
        kwargs = _hidden_quad(board, window)
        if kwargs:
            continue
        kwargs = _omissions(board, window)
        if kwargs:
            continue
        kwargs = _unique_rectangles(board, window)
        if kwargs:
            continue
        kwargs = _x_wings(board, window)
        if kwargs:
            continue
        kwargs = _y_wings(board, window)
        if kwargs:
            continue
        kwargs = _swordfish(board, window)
        if kwargs:
            continue

        if not is_solved(board, window):        # TODO: for debugging only!
            pass
            # print('\nLeaving manual_solver')
        return False
