# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_BOX, CELL_ROW, CELL_COL, CELLS_IN_BOX
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import get_stats, is_clue, get_options, remove_options


@get_stats
def full_house(solver_status, board, window):
    """ A Full House is a row, column or box with a single unsolved cell.
    There is only one missing digit and one empty cell.
    The last candidate is both a Naked Single and a Hidden Single.
    Full Houses are very easy to spot, but they occur mainly when the puzzle is near completion.
    From the algorithmic point of view the technique is used when possible candidates in empty cells
    haven't been calculated yet.
    Rating: 4
    """

    def _set_missing_number(house):
        open_cells = [cell for cell in house if not is_clue(cell, board, solver_status)]
        if len(open_cells) == 1:
            solver_status.capture_baseline(board, window)
            cell_id = open_cells.pop()
            missing_value = SUDOKU_VALUES_SET.copy() - set(
                ''.join(board[cell] for cell in house if is_clue(cell, board, solver_status)))
            assert(len(missing_value) == 1)
            board[cell_id] = missing_value.pop()
            solver_status.clues_found.add(cell_id)
            kwargs["solver_tool"] = "full_house"
            kwargs["new_clue"] = cell_id
            full_house.rating += 4
            full_house.clues += 1
            return True
        return False

    kwargs = {}
    if not solver_status.options_set:
        for i in range(9):
            if (_set_missing_number(CELLS_IN_ROW[i]) or _set_missing_number(CELLS_IN_COL[i]) or
                    _set_missing_number(CELLS_IN_BOX[i])):
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
        if len(with_clue) == 2 and CELL_BOX[with_clue[0]] != CELL_BOX[with_clue[1]]:
            squares = [band + 3*offset if vertical else 3*band + offset for offset in range(3)]
            squares.remove(CELL_BOX[with_clue[0]])
            squares.remove(CELL_BOX[with_clue[1]])
            cells = set(CELLS_IN_BOX[squares[0]])
            if vertical:
                cells -= set(CELLS_IN_COL[CELL_COL[with_clue[0]]]).union(set(CELLS_IN_COL[CELL_COL[with_clue[1]]]))
            else:
                cells -= set(CELLS_IN_ROW[CELL_ROW[with_clue[0]]]).union(set(CELLS_IN_ROW[CELL_ROW[with_clue[1]]]))
            possible_clue_cells = [cell for cell in cells if not is_clue(cell, board, solver_status)]
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
            clue = board[naked_single]
            to_remove = [(clue, cell) for cell in ALL_NBRS[naked_single]
                         if not is_clue(cell, board, solver_status) and clue in board[cell]]
            remove_options(solver_status, board, to_remove, window)
            kwargs["solver_tool"] = "naked_singles"
            kwargs["new_clue"] = naked_single
            kwargs["remove"] = to_remove
            solver_status.clues_found.add(naked_single)
            return kwargs
    else:
        for cell in range(81):
            if board[cell] == ".":
                cell_opts = get_options(cell, board, solver_status)
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
                    cell_opts = get_options(cell, board, solver_status)
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
        if _find_unique_positions(CELLS_IN_BOX[sqr]):
            return kwargs
    return kwargs


