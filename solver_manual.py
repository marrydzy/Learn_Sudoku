# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

import itertools
from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import is_clue, is_solved, get_options


class SolverStatus:
    """ class to store data needed for recovering of puzzle
    status prior to applying a method """
    def __init__(self):
        self.options_set = False
        self.naked_singles = set()
        self.singles = set()
        self.clues = []
        self.options = set()

    def capture(self, window):
        if window:
            self.singles = self.naked_singles.copy()
            self.clues = window.clues_found.copy()
            self.options = window.show_options.copy()

    def restore(self, board, window):
        if window:
            self.naked_singles = self.singles
            window.clues_found = self.clues
            window.show_options = self.options
            for i in range(81):
                board[i] = window.input_board[i]

    def reset(self, board, window):
        self.options_set = False
        self.naked_singles.clear()
        for cell_id in range(81):
            if cell_id not in window.clues_defined:
                board[cell_id] = "."


solver_status = SolverStatus()


def _remove_options(board, to_remove, window):
    """ utility function: removes options as per 'to_remove' list """
    for option, cell in to_remove:
        board[cell] = board[cell].replace(option, "")
        if not board[cell]:
            screwed = [cell]
            # screwed.extend([cell_id for cell_id in ALL_NBRS[cell] if board[cell_id] == option])
            window.critical_error = tuple(screwed)
            window.show_all_pencil_marks = True
            window.set_current_board(board)
        elif len(board[cell]) == 1:
            solver_status.naked_singles.add(cell)


def set_manually(board, window, options_set):
    """ TODO """
    if window and window.clue_entered:
        cell_id = window.clue_entered[0]
        value = window.clue_entered[1]
        window.clue_entered = None

        if board[cell_id] == value and cell_id in window.clues_found:
            if options_set:
                board[cell_id] = ''.join(get_options(cell_id, board, window))
                if len(board[cell_id]) == 1:
                    solver_status.naked_singles.add(cell_id)
            else:
                board[cell_id] = "."
            window.clues_found.remove(cell_id)
            window.set_current_board(board)
        else:
            conflicting_cells = [cell for cell in ALL_NBRS[cell_id] if board[cell] == value]
            if conflicting_cells:
                conflicting_cells.append(cell_id)
                window.conflicting_cells = conflicting_cells
                window.clue_house = ALL_NBRS[cell_id]
                window.previous_cell_value = (cell_id, board[cell_id])
            else:
                board[cell_id] = value
                window.clues_found.add(cell_id)
                if cell_id in solver_status.naked_singles:
                    solver_status.naked_singles.remove(cell_id)
                if options_set:
                    to_remove = [(value, cell) for cell in ALL_NBRS[cell_id] if value in board[cell]]
                    _remove_options(board, to_remove, window)
                window.set_current_board(board)
        return True
    return False


def _open_singles(board, window, options_set=False):
    """ 'Open Singles' technique (see: https://www.learn-sudoku.com/open-singles.html)
        The technique is applicable only in the initial phase of sudoku solving process when
        options in empty cells haven't been calculated yet.
    """

    def _set_missing_number(house):
        open_cells = [cell for cell in house if not is_clue(cell, board, window)]
        if len(open_cells) == 1:
            missing_value = SUDOKU_VALUES_SET.copy() - set(''.join([board[cell] for cell in house]))
            if len(missing_value) != 1:
                board[open_cells[0]] = ''.join(missing_value)
                value_cells = defaultdict(list)
                for cell in house:
                    value_cells[board[cell]].append(cell)
                screwed = [open_cells[0]]
                for value, cell in value_cells.items():
                    if len(cell) != 1:
                        screwed.extend(cell)
                window.critical_error = tuple(screwed)
                window.show_all_pencil_marks = True
                window.set_current_board(board)
            else:
                board[open_cells[0]] = missing_value.pop()
            if window:
                if window.draw_board(board, "open_singles", new_clue=open_cells[0]):
                    window.clues_found.add(open_cells[0])
                else:
                    solver_status.restore(board, window)
            return True
        return False

    if not options_set:
        for i in range(9):
            if (_set_missing_number(CELLS_IN_ROW[i]) or _set_missing_number(CELLS_IN_COL[i]) or
                    _set_missing_number(CELLS_IN_SQR[i])):
                return True
    return False


def _visual_elimination(board, window, options_set=False):
    """ 'Visual Elimination' techniques (see: https://www.learn-sudoku.com/visual-elimination.html)
        The technique is applicable only in the initial phase of sudoku solving process when
        options in empty cells haven't been calculated yet.
        After finding a clue The function returns to the main solver loop to allow trying 'simpler'
        'open singles' method
    """
    if options_set:
        return False

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
                board[clues[0]] = value
                if window:
                    house = [cell for offset in range(3) for cell in cols_rows[3*band + offset]]
                    if window.draw_board(board, "visual_elimination", house=house, new_clue=clues[0],
                                         greyed_out=greyed_out):
                        window.clues_found.add(clues[0])
                    else:
                        solver_status.restore(board, window) # TODO: tutaj jest problem!!!
                return True
        return False

    for value in SUDOKU_VALUES_LIST:
        for zone in range(6):
            if _check_zone(value, zone):
                return True
    return False


def _naked_singles(board, window, options_set=False):
    """ 'Naked Singles' technique (see: https://www.learn-sudoku.com/lone-singles.html)
        In the initial phase of sudoku solving when options of all unsolved cells are not set yet,
        after finding a clue the function returns to the main solver loop to allow trying 'simpler'
        methods ('open singles' and then 'visual elimination').
        When options for all unsolved cells are already set the function continues solving naked singles until
        the 'naked_singles' list is empty (at this stage of sudoku solving it is the 'simplest' method)
    """
    if options_set:
        if not solver_status.naked_singles:
            return False
        else:
            naked_single = solver_status.naked_singles.pop()
            clue = board[naked_single]
            to_remove = [(clue, cell) for cell in ALL_NBRS[naked_single] if clue in board[cell]]
            _remove_options(board, to_remove, window)
            if window:
                if window.draw_board(board, "naked_singles", new_clue=naked_single, remove=to_remove):
                    window.clues_found.add(naked_single)
                else:
                    solver_status.restore(board, window)
            return True
    else:
        for cell in range(81):
            if board[cell] == ".":
                cell_opts = get_options(cell, board, window)
                if len(cell_opts) == 1:
                    board[cell] = cell_opts.pop()
                    if window and window.draw_board(board, "naked_singles", new_clue=cell):
                        window.clues_found.add(cell)
                    return True
        return False


def _hidden_singles(board, window, options_set=False):
    """ 'Hidden Singles' technique (see: https://www.learn-sudoku.com/hidden-singles.html) """

    def _find_unique_positions(house):
        """ Find unique positions of missing clues within the house and 'solve' the cells """
        if options_set:
            house_options = set(''.join(board[cell_id] for cell_id in house if len(board[cell_id]) > 1))
        else:
            house_options = SUDOKU_VALUES_SET.copy() - set(''.join([board[cell_id] for cell_id in house]))
        for option in house_options:
            in_cells = []
            greyed_out = []
            to_remove = []
            show_options = window.show_options if window else list()
            for cell in house:
                if board[cell] == ".":
                    cell_opts = get_options(cell, board, window)
                    if option in cell_opts:
                        in_cells.append(cell)
                    else:
                        greyed_out.append(cell)
                elif options_set and len(board[cell]) > 1:
                    if option in board[cell]:
                        in_cells.append(cell)
                    elif cell not in show_options:
                        greyed_out.append(cell)

            if len(in_cells) == 1:
                clue_id = in_cells[0]
                board[clue_id] = option
                if options_set:
                    to_remove = [(option, cell) for cell in ALL_NBRS[clue_id] if option in board[cell]]
                    _remove_options(board, to_remove, window)
                if window:
                    if window.draw_board(board, "hidden_singles", new_clue=clue_id,
                                                house=house, greyed_out=greyed_out, remove=to_remove):
                        window.clues_found.add(clue_id)
                    else:
                        solver_status.restore(board, window)
                return True
        return False

    for row in range(9):
        if _find_unique_positions(CELLS_IN_ROW[row]):
            return True
    for col in range(9):
        if _find_unique_positions(CELLS_IN_COL[col]):
            return True
    for sqr in range(9):
        if _find_unique_positions(CELLS_IN_SQR[sqr]):
            return True
    return False


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
                    _remove_options(board, to_remove, window)
                    if window:
                        if window.draw_board(board, "hidden_pairs", remove=to_remove, claims=in_cells, house=cells):
                            pass
                        else:
                            solver_status.restore(board, window)
                    return True
        return False

    for i in range(9):
        if _find_pairs(CELLS_IN_ROW[i]):
            return True
    for i in range(9):
        if _find_pairs(CELLS_IN_COL[i]):
            return True
    for i in range(9):
        if _find_pairs(CELLS_IN_SQR[i]):
            return True
    return False


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
                    _remove_options(board, to_remove, window)
                    if window:
                        if window.draw_board(board, "hidden_triplets", remove=to_remove,
                                             claims=triplet_cells, house=cells):
                            pass
                        else:
                            solver_status.restore(board, window)
                    return True
        return False

    for i in range(9):
        if _find_triplets(CELLS_IN_ROW[i]):
            return True
        if _find_triplets(CELLS_IN_COL[i]):
            return True
        if _find_triplets(CELLS_IN_SQR[i]):
            return True
    return False


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
                    _remove_options(board, to_remove, window)
                    if window:
                        if window.draw_board(board, "hidden_quads", remove=to_remove, claims=quad_cells, house=cells):
                            pass
                        else:
                            solver_status.restore(board, window)
                    return True
        return False

    for i in range(9):
        if _find_quad(CELLS_IN_ROW[i]):
            return True
        if _find_quad(CELLS_IN_COL[i]):
            return True
        if _find_quad(CELLS_IN_SQR[i]):
            return True
    return False


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
                window.show_all_pencil_marks = True
                print('\nDupa_3')
                # raise DeadEndException
            elif len(in_cells) == 2:
                unsolved.remove(in_cells[0])
                unsolved.remove(in_cells[1])
                to_remove = [(values[0], cell) for cell in unsolved if values[0] in board[cell]]
                to_remove.extend([(values[1], cell) for cell in unsolved if values[1] in board[cell]])
                if to_remove:
                    _remove_options(board, to_remove, window)
                    if window:
                        if window.draw_board(board, "naked_twins", remove=to_remove, claims=in_cells, house=cells):
                            pass
                        else:
                            solver_status.restore(board, window)
                    return True
        return False

    for i in range(9):
        if _find_pairs(CELLS_IN_ROW[i]):
            return True
        if _find_pairs(CELLS_IN_COL[i]):
            return True
        if _find_pairs(CELLS_IN_SQR[i]):
            return True
    return False


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
                        _remove_options(board, to_remove, window)
                        if window:
                            if window.draw_board(board, "naked_triplets", remove=to_remove,
                                                 laims=triplet, house=cells):
                                pass
                            else:
                                solver_status.restore(board, window)
                        return True
        return False

    for i in range(9):
        if _find_triplets(CELLS_IN_ROW[i]):
            return True
        if _find_triplets(CELLS_IN_COL[i]):
            return True
        if _find_triplets(CELLS_IN_SQR[i]):
            return True
    # else:
        # return True if naked_triplets.board_updated else None
    return False


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
                        _remove_options(board, to_remove, window)
                        if window:
                            if window.draw_board(board, "naked_quads", remove=to_remove, claims=quad, house=cells):
                                pass
                            else:
                                solver_status.restore(board, window)
                        return True
        return False

    for i in range(9):
        if _find_quad(CELLS_IN_ROW[i]):
            return True
        if _find_quad(CELLS_IN_COL[i]):
            return True
        if _find_quad(CELLS_IN_SQR[i]):
            return True
    # else:
        # return True if naked_triplets.board_updated else None
    return False


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
                        _remove_options(board, to_remove, window)
                        if window:
                            claims = [(to_remove[0][0], cell) for cell in cells]
                            if window.draw_board(board, "omissions", claims=claims, remove=to_remove,
                                                 house=cells, impacted_cells=impacted_cells):
                                pass
                            else:
                                solver_status.restore(board, window)
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
                    _remove_options(board, to_remove, window)
                    if window:
                        claims = [(to_remove[0][0], cell) for cell in cells]
                        if window.draw_board(board, "omissions", claims=claims, remove=to_remove,
                                             house=cells, impacted_cells=impacted_cells):
                            pass
                        else:
                            solver_status.restore(board, window)
                    return True
        return False

    for i in range(9):
        if _in_row_col(CELLS_IN_ROW[i]):
            return True
        if _in_row_col(CELLS_IN_COL[i]):
            return True
        if _in_block(CELLS_IN_SQR[i]):
            return True

    return False


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
                _remove_options(board, to_remove, window)
                if window:
                    if window.draw_board(board, "y_wings", y_wing=wing, remove=to_remove,
                                         impacted_cells=set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]])):
                        pass
                    else:
                        solver_status.restore(board, window)
                return True
        return False

    for cell in range(81):
        if len(board[cell]) == 2 and _reduce_xs(_find_wings(cell)):
            return True
    return False


def init_options(board, window):
    """ Initialize options of unsolved cells """
    if not solver_status.options_set:
        for cell in range(81):
            # if board[cell] == ".":
            if not is_clue(cell, board, window):
                nbr_clues = [board[nbr_cell] for nbr_cell in ALL_NBRS[cell] if is_clue(nbr_cell, board, window)]
                board[cell] = "".join(value for value in SUDOKU_VALUES_LIST if value not in nbr_clues)
                if len(board[cell]) == 1:
                    solver_status.naked_singles.add(cell)
        if window:
            window.set_current_board(board)
            solver_status.capture(window)
        solver_status.options_set = True


def manual_solver(board, window, _):
    """ TODO - manual solver """

    while True:
        if is_solved(board, window):
            return True
        solver_status.capture(window)
        if set_manually(board, window, solver_status.options_set):
            continue
        if _open_singles(board, window, solver_status.options_set):
            continue
        if _visual_elimination(board, window, solver_status.options_set):
            continue
        if _naked_singles(board, window, solver_status.options_set):
            continue
        if _hidden_singles(board, window, solver_status.options_set):
            continue

        init_options(board, window)
        if _hidden_pair(board, window):
            continue
        if _naked_twins(board, window):
            continue
        if _omissions(board, window):
            continue
        if _y_wings(board, window):
            continue
        hidden_triplet = _hidden_triplet(board, window)
        if _naked_triplets(board, window):
            continue
        elif hidden_triplet:
            continue
        hidden_quad = _hidden_quad(board, window)
        if _naked_quads(board, window):
            continue
        elif hidden_quad:
            continue

        return True
