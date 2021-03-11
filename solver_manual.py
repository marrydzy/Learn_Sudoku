# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

import itertools
from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import is_clue, is_solved, get_options, DeadEndException
import pygame

naked_singles = []


def _remove_options(board, to_remove):
    """ utility function: removes options as per 'to_remove' list """
    for option, cell in to_remove:
        board[cell] = board[cell].replace(option, "")
        if not board[cell]:
            raise DeadEndException
        elif len(board[cell]) == 1:
            naked_singles.append(cell)


def set_manually(board, window, options_set=False):
    """ TODO """
    if window and window.clue_entered:
        cell_id = window.clue_entered[0]
        value = window.clue_entered[1]
        window.clue_entered = None
        conflicting_cells = [cell for cell in ALL_NBRS[cell_id] if board[cell] == value]
        if conflicting_cells:
            conflicting_cells.append(cell_id)
            window.conflicting_cells = conflicting_cells
            window.clue_house = ALL_NBRS[cell_id]
            window.previous_cell_value = (cell_id, board[cell_id])
        else:
            board[cell_id] = value
            window.clues_found.append(cell_id)
            window.set_current_board(board)


def _open_singles(board, window, options_set=False):
    """ 'Open Singles' technique (see: https://www.learn-sudoku.com/open-singles.html)
        The technique is applicable only in the initial phase of sudoku solving process when
        options in empty cells haven't been calculated yet.
    """

    def _set_missing_number(house):
        open_cells = [cell for cell in house if not is_clue(board[cell])]
        if len(open_cells) == 1:
            missing_value = SUDOKU_VALUES_SET.copy() - set(''.join([board[cell] for cell in house]))
            if len(missing_value) != 1:
                raise DeadEndException
            board[open_cells[0]] = missing_value.pop()
            if window and window.draw_board(board, "open_singles", options_set=options_set,
                                            singles=open_cells, new_clue=open_cells[0]):
                window.clues_found.append(open_cells[0])
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
        if len(with_clue) == 2:
            squares = [band + 3*offset if vertical else 3*band + offset for offset in range(3)]
            squares.remove(CELL_SQR[with_clue[0]])
            squares.remove(CELL_SQR[with_clue[1]])
            cells = set(CELLS_IN_SQR[squares[0]])
            if vertical:
                cells -= set(CELLS_IN_COL[CELL_COL[with_clue[0]]]).union(set(CELLS_IN_COL[CELL_COL[with_clue[1]]]))
            else:
                cells -= set(CELLS_IN_ROW[CELL_ROW[with_clue[0]]]).union(set(CELLS_IN_ROW[CELL_ROW[with_clue[1]]]))
            possible_clue_cells = [cell for cell in cells if not is_clue(board[cell])]
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
                    if window.draw_board(board, "visual_elimination", options_set=options_set,
                                         house=house, singles=with_clue, new_clue=clues[0],
                                         greyed_out=greyed_out):
                        window.clues_found.append(clues[0])
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
        After finding a clue The function returns to the main solver loop to allow trying 'simpler'
        methods ('open singles' and then 'visual elimination'
        When options for all unsolved cells are already set the function continues solving naked singles until
        the 'naked_singles' list is empty (at this stage of sudoku solving it is the 'simplest' method)
    """
    if options_set:
        if not naked_singles:
            return False
        while naked_singles:
            naked_single = naked_singles.pop()
            clue = board[naked_single]
            to_remove = [(clue, cell) for cell in ALL_NBRS[naked_single] if clue in board[cell]]
            _remove_options(board, to_remove)
            if window and window.draw_board(board, "naked_singles", options_set=options_set, new_clue=naked_single,
                                            remove=to_remove, naked_singles=naked_singles):
                window.clues_found.append(naked_single)
        return True
    else:
        for cell in range(81):
            if board[cell] == ".":
                cell_opts = get_options(board, cell)
                if len(cell_opts) == 1:
                    board[cell] = cell_opts.pop()
                    if window and window.draw_board(board, "naked_singles", options_set=options_set,
                                                    singles=[cell], new_clue=cell):
                        window.clues_found.append(cell)
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
            for cell in house:
                if not options_set and board[cell] == ".":
                    cell_opts = get_options(board, cell)
                    if option in cell_opts:
                        in_cells.append(cell)
                    else:
                        greyed_out.append(cell)
                if options_set and option in board[cell]:
                    in_cells.append(cell)

            if len(in_cells) == 1:
                board[in_cells[0]] = option
                # if window:    TODO!
                #     window.set_current_board(board)     # to properly display the hidden single
                if options_set:
                    to_remove = [(option, cell) for cell in ALL_NBRS[in_cells[0]] if option in board[cell]]
                    _remove_options(board, to_remove)
                if window and window.draw_board(board, "hidden_singles", options_set=options_set,
                                                singles=[in_cells[0]], new_clue=in_cells[0],
                                                house=house, greyed_out=greyed_out, remove=to_remove):
                    window.clues_found.append(in_cells[0])
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


def _hidden_pairs(board, window):
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
                    _remove_options(board, to_remove)
                    if window:
                        window.draw_board(board, "hidden_pairs", remove=to_remove,
                                          subset=in_cells, house=cells, options_set=True)
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


def _hidden_triplets(board, window):
    """When three given pencil marks appear in only three cells
    in any given row, column, or block, all other pencil marks may be removed
    from those cells.
    (see https://www.learn-sudoku.com/hidden-triplets.html)
    """

    def _find_triplets(cells):
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        options = set("".join(board[cell] for cell in unsolved))
        if len(unsolved) < 4 or len(options) < 4:
            return

        options_dic = {value: {cell for cell in unsolved if value in board[cell]} for value in options}
        for triplet in itertools.combinations(options, 3):
            triplet_cells = set()
            for value in triplet:
                triplet_cells = triplet_cells.union(options_dic[value])
            if len(triplet_cells) == 3:
                remove_opts = set("".join(board[cell] for cell in triplet_cells)) - set(triplet)
                to_remove = [(value, cell) for value in remove_opts for cell in triplet_cells]
                if to_remove:
                    _remove_options(board, to_remove)
                    if window:
                        window.draw_board(board, "hidden_triplets", remove=to_remove,
                                          subset=triplet_cells, house=cells, options_set=True)
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


def _naked_twins(board, window):
    """For each 'house' (row, column or square) find twin cells with two options
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
                raise DeadEndException
            elif len(in_cells) == 2:
                unsolved.remove(in_cells[0])
                unsolved.remove(in_cells[1])
                to_remove = [(values[0], cell) for cell in unsolved if values[0] in board[cell]]
                to_remove.extend([(values[1], cell) for cell in unsolved if values[1] in board[cell]])
                if to_remove:
                    _remove_options(board, to_remove)
                    if window:
                        window.draw_board(board, "naked_twins", remove=to_remove, subset=in_cells, house=cells,
                                          naked_singles=naked_singles, options_set=True)
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
                    other_cells = set(CELLS_IN_SQR[squares.pop()]) - set(cells)
                    to_remove = [(value, cell) for cell in other_cells if value in board[cell]]
                    if to_remove:
                        _remove_options(board, to_remove)
                        if window:
                            claims = [(to_remove[0][0], cell) for cell in cells]
                            window.draw_board(board, "omissions", claims=claims, remove=to_remove,
                                              singles=naked_singles, house=cells, other_cells=other_cells,
                                              options_set=True)
                        return True
        return False

    def _in_block(cells):
        options = SUDOKU_VALUES_SET - {board[cell] for cell in cells if len(board[cell]) == 1}
        for value in options:
            unsolved = {cell for cell in cells if len(board[cell]) > 1}
            in_rows = set(CELL_ROW[cell] for cell in unsolved if value in board[cell])
            in_cols = set(CELL_COL[cell] for cell in unsolved if value in board[cell])
            if len(in_rows) == 1 or len(in_cols) == 1:
                other_cells = set()
                if len(in_rows) == 1:
                    other_cells = set(CELLS_IN_ROW[in_rows.pop()]) - set(cells)
                elif len(in_cols) == 1:
                    other_cells = set(CELLS_IN_COL[in_cols.pop()]) - set(cells)
                to_remove = [(value, cell) for cell in other_cells if value in board[cell]]
                if to_remove:
                    _remove_options(board, to_remove)
                    if window:
                        claims = [(to_remove[0][0], cell) for cell in cells]
                        window.draw_board(board, "omissions", claims=claims, remove=to_remove,
                                          singles=naked_singles, house=cells, other_cells=other_cells,
                                          options_set=True)
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
                _remove_options(board, to_remove)
                if window:
                    window.draw_board(board, "y_wings", y_wing=wing, singles=naked_singles, remove=to_remove,
                                      other_cells=set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]]),
                                      options_set=True)
                return True
        return False

    for cell in range(81):
        if len(board[cell]) == 2 and _reduce_xs(_find_wings(cell)):
            return True
    return False


def _init_options(board, window):
    """ Initialize options of unsolved cells """
    for cell in range(81):
        if board[cell] == ".":
            nbr_clues = [board[nbr_cell] for nbr_cell in ALL_NBRS[cell] if is_clue(board[nbr_cell])]
            board[cell] = "".join(value for value in SUDOKU_VALUES_LIST if value not in nbr_clues)
    if window:
        window.set_current_board(board)


def manual_solver(board, window, _):
    """ TODO - manual solver """

    options_set = False
    while True:
        if is_solved(board):
            return True
        set_manually(board, window, options_set)
        if _open_singles(board, window, options_set):
            continue
        if _visual_elimination(board, window, options_set):
            continue
        if _naked_singles(board, window, options_set):
            continue
        if _hidden_singles(board, window, options_set):
            continue
        if not options_set:
            _init_options(board, window)
            options_set = True
        if _hidden_pairs(board, window):
            continue
        if _naked_twins(board, window):
            continue
        if _omissions(board, window):
            continue
        if _y_wings(board, window):
            continue
        if _hidden_triplets(board, window):
            continue

        return True

