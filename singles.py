# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_BOX, CELL_ROW, CELL_COL, CELLS_IN_BOX
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import get_stats, is_clue, get_options, remove_options, init_options


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
            missing_value = SUDOKU_VALUES_SET - set(
                ''.join(board[cell] for cell in house if is_clue(cell, board, solver_status)))
            board[cell_id] = missing_value.pop()
            solver_status.clues_found.add(cell_id)
            kwargs["solver_tool"] = "full_house"
            kwargs["new_clue"] = cell_id
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


@get_stats
def visual_elimination(solver_status, board, window):
    """ 'Visual Elimination' techniques (see: https://www.learn-sudoku.com/visual-elimination.html)
    The technique is applied in the initial phase of sudoku solving process when
    unresolved cells candidates haven't been calculated yet.
    If a clue is found it is also Hidden Single; however, the technique is kept separate
    in order to mimic 'manual' way of solving sudoku
    Rating: 4
    """
    def _check_zone(value, band):
        """ Look for lone singles in the band (vertical or horizontal stack of boxes) """
        vertical = True if band < 3 else False
        band = band % 3
        cols_rows = CELLS_IN_COL if vertical else CELLS_IN_ROW
        with_clue = [cell for offset in range(3) for cell in cols_rows[3*band + offset] if board[cell] == value]
        if len(with_clue) == 2 and CELL_BOX[with_clue[0]] != CELL_BOX[with_clue[1]]:
            boxes = [band + 3*offset if vertical else 3*band + offset for offset in range(3)]
            boxes.remove(CELL_BOX[with_clue[0]])
            boxes.remove(CELL_BOX[with_clue[1]])
            cells = set(CELLS_IN_BOX[boxes.pop()])
            if vertical:
                other_cells = set(CELLS_IN_COL[CELL_COL[with_clue[0]]]).union(set(CELLS_IN_COL[CELL_COL[with_clue[1]]]))
            else:
                other_cells = set(CELLS_IN_ROW[CELL_ROW[with_clue[0]]]).union(set(CELLS_IN_ROW[CELL_ROW[with_clue[1]]]))
            greyed_out = {cell for cell in cells.intersection(other_cells) if not is_clue(cell, board, solver_status)}
            cells = cells.difference(other_cells)
            possible_clue_cells = [cell for cell in cells if not is_clue(cell, board, solver_status)]
            clues = []
            for cell in possible_clue_cells:
                if vertical:
                    other_clue = [cell_id for cell_id in CELLS_IN_ROW[CELL_ROW[cell]] if board[cell_id] == value]
                else:
                    other_clue = [cell_id for cell_id in CELLS_IN_COL[CELL_COL[cell]] if board[cell_id] == value]
                if other_clue:
                    with_clue.append(other_clue[0])
                    greyed_out.add(cell)
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
                visual_elimination.clues += 1
                return True
        return False

    kwargs = {}
    if not solver_status.options_set:
        for digit in SUDOKU_VALUES_LIST:
            for zone in range(6):
                if _check_zone(digit, zone):
                    return kwargs
    return kwargs


@get_stats
def naked_singles(solver_status, board, window):
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
    if not (window or solver_status.options_set):
        init_options(board, solver_status)
        naked_singles.clues += len(solver_status.naked_singles)

    if solver_status.options_set:
        if not solver_status.naked_singles:
            return kwargs
        else:
            naked_singles_in = len(solver_status.naked_singles)
            solver_status.capture_baseline(board, window)
            naked_single = solver_status.naked_singles.pop()
            clue = board[naked_single]
            to_remove = {(clue, cell) for cell in ALL_NBRS[naked_single] if clue in board[cell]}
            remove_options(solver_status, board, to_remove, window)
            kwargs["solver_tool"] = "naked_singles"
            kwargs["new_clue"] = naked_single
            kwargs["remove"] = to_remove
            solver_status.clues_found.add(naked_single)
            naked_singles.options_removed += len(to_remove)
            naked_singles.clues += len(solver_status.naked_singles) - naked_singles_in + 1
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
                    naked_singles.clues += 1
                    return kwargs
        return kwargs


@get_stats
def hidden_singles(solver_status, board, window):
    """ A Hidden Single is a single candidate remaining for a specific digit in a row, column or box.
    'Hidden Singles' technique (see: https://www.learn-sudoku.com/hidden-singles.html)
    Rating: 6 - 20
    """

    def _find_hidden_single(house):
        """ Find unique positions of missing clues within the house and 'solve' the cells """
        if solver_status.options_set:
            house_options = set(''.join(board[cell_id] for cell_id in house if len(board[cell_id]) > 1))
        else:
            house_options = SUDOKU_VALUES_SET - set(''.join([board[cell_id] for cell_id in house]))
        unsolved = {cell for cell in house if len(board[cell]) > 1 or board[cell] == "."}
        for option in house_options:
            if solver_status.options_set:
                in_cells = {cell for cell in unsolved if option in board[cell]}
            else:
                in_cells = {cell for cell in unsolved if option in get_options(cell, board, solver_status)}
            if len(in_cells) == 1:
                solver_status.capture_baseline(board, window)
                clue_id = in_cells.pop()
                board[clue_id] = option
                solver_status.clues_found.add(clue_id)
                to_remove = set()
                if solver_status.options_set:
                    to_remove = {(option, cell) for cell in ALL_NBRS[clue_id] if option in board[cell]}
                    remove_options(solver_status, board, to_remove, window)
                if window and solver_status.options_set:
                    window.options_visible = window.options_visible.union(house)
                options_visible = window.options_visible if window else set()
                greyed_out = {cell for cell in house if not is_clue(cell, board, solver_status) and
                              cell not in options_visible}
                kwargs["solver_tool"] = "hidden_singles"
                kwargs["new_clue"] = clue_id
                kwargs["greyed_out"] = greyed_out
                kwargs["remove"] = to_remove
                kwargs["house"] = {cell for cell in house if len(board[cell]) > 1}
                hidden_singles.clues += 1 + len(solver_status.naked_singles)
                hidden_singles.options_removed += len(to_remove)
                return True
        return False

    kwargs = {}
    for idx in range(9):
        if _find_hidden_single(CELLS_IN_ROW[idx]) or \
                _find_hidden_single(CELLS_IN_COL[idx]) or \
                _find_hidden_single(CELLS_IN_BOX[idx]):
            break
    return kwargs


