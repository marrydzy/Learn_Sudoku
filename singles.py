# -*- coding: UTF-8 -*-

""" 'SINGLES' CLASS OF SOLVING METHODS
    GLOBAL FUNCTIONS:
        full_house() - when there is a row, column or box with a single unsolved cell
        visual_elimination() - basic technique of finding hidden singles
        naked_single() - when there is only one (remaining) candidate in a cell
        hidden_single() - when there is only one single candidate remaining for a specific digit in a row, column or box

TODO:
"""

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_BOX, CELL_ROW, CELL_COL, CELLS_IN_BOX
from utils import SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import get_stats, is_digit, get_cell_candidates, set_remaining_candidates, get_impacted_houses
from utils import place_digit, get_impacting_cells


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
        unsolved_cells = [cell for cell in house if not is_digit(cell, board, solver_status)]
        if len(unsolved_cells) == 1:
            solver_status.capture_baseline(board, window)
            cell = unsolved_cells.pop()
            missing_digit = SUDOKU_VALUES_SET - set(
                ''.join(board[cell] for cell in house if is_digit(cell, board, solver_status)))
            board[cell] = missing_digit.pop()
            solver_status.cells_solved.add(cell)
            kwargs["solver_tool"] = full_house.__name__
            kwargs["house"] = house
            kwargs["cell_solved"] = cell
            full_house.clues += 1
            return True
        return False

    kwargs = {}
    if not solver_status.pencilmarks:
        for i in range(9):
            if (_set_missing_number(CELLS_IN_ROW[i]) or _set_missing_number(CELLS_IN_COL[i]) or
                    _set_missing_number(CELLS_IN_BOX[i])):
                break
    return kwargs


@get_stats
def visual_elimination(solver_status, board, window):
    """ 'Visual Elimination' techniques (see: https://www.learn-sudoku.com/visual-elimination.html)
    The technique is applied in the initial phase of sudoku solving process when
    unresolved cells candidates haven't been calculated yet.
    If a clue is found it is also Hidden Single; however, the technique is kept separate
    in order to mimic 'manual' way of solving sudoku
    Rating: 4
    """
    def _check_zone(value, chute):
        """ Look for lone singles in the chute (vertical or horizontal stack of boxes) """
        vertical = True if chute < 3 else False
        chute = chute % 3
        cols_rows = CELLS_IN_COL if vertical else CELLS_IN_ROW
        house = {cell for offset in range(3) for cell in cols_rows[3 * chute + offset]}
        with_value = [cell for cell in house if board[cell] == value]
        if len(with_value) == 2 and CELL_BOX[with_value[0]] != CELL_BOX[with_value[1]]:
            boxes = [chute + 3*offset if vertical else 3*chute + offset for offset in range(3)]
            boxes.remove(CELL_BOX[with_value[0]])
            boxes.remove(CELL_BOX[with_value[1]])
            box_cells = set(CELLS_IN_BOX[boxes.pop()])
            if vertical:
                other_cells = set(CELLS_IN_COL[CELL_COL[with_value[0]]]).union(CELLS_IN_COL[CELL_COL[with_value[1]]])
            else:
                other_cells = set(CELLS_IN_ROW[CELL_ROW[with_value[0]]]).union(CELLS_IN_ROW[CELL_ROW[with_value[1]]])
            possibilities = set()
            greyed_out = set()
            for cell in {cell for cell in box_cells.difference(other_cells)
                         if not is_digit(cell, board, solver_status)}:
                if vertical:
                    interacting = {cell_id for cell_id in CELLS_IN_ROW[CELL_ROW[cell]] if board[cell_id] == value}
                else:
                    interacting = {cell_id for cell_id in CELLS_IN_COL[CELL_COL[cell]] if board[cell_id] == value}
                if interacting:
                    assert len(interacting) == 1
                    with_value.append(interacting.pop())
                    greyed_out.add(cell)
                else:
                    possibilities.add(cell)
            if len(possibilities) == 1:
                solver_status.capture_baseline(board, window)
                cell_solved = possibilities.pop()
                board[cell_solved] = value
                solver_status.cells_solved.add(cell_solved)
                kwargs["solver_tool"] = visual_elimination.__name__
                kwargs["cell_solved"] = cell_solved
                kwargs["greyed_out"] = greyed_out
                kwargs["chain_a"] = {cell: set() for cell in with_value}
                kwargs["house"] = house
                visual_elimination.clues += 1
                return True
        return False

    kwargs = {}
    if not solver_status.pencilmarks:
        for digit in SUDOKU_VALUES_LIST:
            for zone in range(6):
                if _check_zone(digit, zone):
                    return kwargs
    return kwargs


@get_stats
def naked_single(solver_status, board, window):
    """ A naked single is the last remaining candidate in a cell.
    The Naked Single is categorized as a solving technique but you can hardly
    call it a technique. The only 'real work' is done when candidates in unsolved
    cells are not calculated yet: then the algorithm checks all possible candidates
    for each such cell to find the one with only one candidate.
    Otherwise, a naked single is that what remains after you have applied
    your solving techniques, by eliminating other candidates.
    Alternative terms are Forced Digit and Sole Candidate.
    Rating: 4
    """
    kwargs = {}
    if not (window or solver_status.pencilmarks):
        set_remaining_candidates(board, solver_status)
        naked_single.clues += len(solver_status.naked_singles)

    if solver_status.pencilmarks:
        if not solver_status.naked_singles:
            return None
        else:
            naked_singles_on_entry = len(solver_status.naked_singles)
            the_single = list(solver_status.naked_singles)[0]
            eliminate, impacted_cells = place_digit(the_single, board[the_single], board, solver_status, window)
            naked_single.options_removed += len(eliminate)
            naked_single.clues += len(solver_status.naked_singles) - naked_singles_on_entry + 1
            kwargs["solver_tool"] = naked_single.__name__
            if window:
                kwargs["cell_solved"] = the_single
                kwargs["eliminate"] = eliminate
                kwargs["house"] = get_impacted_houses(the_single, base_house=None, to_eliminate=impacted_cells)
            return kwargs
    else:
        for cell in range(81):
            if board[cell] == ".":
                cell_opts = get_cell_candidates(cell, board, solver_status)
                if len(cell_opts) == 1:
                    solver_status.capture_baseline(board, window)
                    board[cell] = cell_opts.pop()
                    kwargs["solver_tool"] = naked_single.__name__
                    kwargs["cell_solved"] = cell
                    solver_status.cells_solved.add(cell)
                    naked_single.clues += 1
                    return kwargs
        return kwargs


@get_stats
def hidden_single(solver_status, board, window):
    """ A Hidden Single is a single candidate remaining for a specific digit in a row, column or box.
    'Hidden Singles' technique (see: https://www.learn-sudoku.com/hidden-singles.html)
    Rating: 6 - 20
    """

    def _find_hidden_single(house):
        """ Find unique positions of missing clues within the house and 'solve' the cells """
        house = set(house)
        if solver_status.pencilmarks:
            house_candidates = set(''.join(board[cell_id] for cell_id in house if len(board[cell_id]) > 1))
        else:
            house_candidates = SUDOKU_VALUES_SET - set(''.join([board[cell_id] for cell_id in house]))
        unsolved = {cell for cell in house if len(board[cell]) > 1 or board[cell] == "."}
        for candidate in house_candidates:
            if solver_status.pencilmarks:
                in_cells = {cell for cell in unsolved if candidate in board[cell]}
            else:
                in_cells = {cell for cell in unsolved if candidate in get_cell_candidates(cell, board, solver_status)}
            if len(in_cells) == 1:
                cell_solved = in_cells.pop()
                eliminate, impacted_cells = place_digit(cell_solved, candidate, board, solver_status, window)
                hidden_single.clues += 1 + len(solver_status.naked_singles)
                hidden_single.options_removed += len(eliminate)
                kwargs["solver_tool"] = hidden_single.__name__
                if window:
                    if solver_status.pencilmarks:
                        window.options_visible = window.options_visible.union(house)
                    greyed_out = {cell for cell in house if not is_digit(cell, board, solver_status) and
                                  cell not in window.options_visible}
                    kwargs["house"] = get_impacted_houses(cell_solved, base_house=house, to_eliminate=impacted_cells)
                    kwargs["cell_solved"] = cell_solved
                    kwargs["greyed_out"] = greyed_out
                    kwargs["eliminate"] = eliminate
                    kwargs["chain_a"] = {cell: set() for cell in get_impacting_cells(candidate, greyed_out, board)}
                return True
        return False

    kwargs = {}
    for idx in range(9):
        if _find_hidden_single(CELLS_IN_ROW[idx]) or \
                _find_hidden_single(CELLS_IN_COL[idx]) or \
                _find_hidden_single(CELLS_IN_BOX[idx]):
            break
    return kwargs
