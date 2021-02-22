# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import is_clue, is_solved, get_options, are_cells_set, DeadEndException

naked_singles = []


def _open_singles(board, window, options_set=False):
    """ 'Open Singles' technique (see: https://www.learn-sudoku.com/open-singles.html)
        The technique is applicable only in the initial phase of sudoku solving process when
        options in empty cells haven't been calculated yet.
    """
    if options_set:
        return False

    def _set_missing_number(house):
        open_cells = [cell for cell in house if not is_clue(board[cell])]
        if len(open_cells) == 1:
            _open_singles.clue_found = True
            missing_value = SUDOKU_VALUES_SET.copy() - set(''.join([board[cell] for cell in house]))
            if len(missing_value) != 1:
                raise DeadEndException
            board[open_cells[0]] = missing_value.pop()
            if window:
                window.draw_board(board, "open_singles", options_set=False,
                                  singles=open_cells, new_clue=open_cells[0])

    board_updated = False
    _open_singles.clue_found = True
    while _open_singles.clue_found:
        _open_singles.clue_found = False
        for row in range(9):
            _set_missing_number(CELLS_IN_ROW[row])
        for col in range(9):
            _set_missing_number(CELLS_IN_COL[col])
        for sqr in range(9):
            _set_missing_number(CELLS_IN_SQR[sqr])
        if _open_singles.clue_found:
            board_updated = True
    return board_updated


def _visual_elimination(board, window, options_set=False):
    """ 'Visual Elimination' techniques (see: https://www.learn-sudoku.com/visual-elimination.html)
        The technique is applicable only in the initial phase of sudoku solving process when
        options in empty cells haven't been calculated yet.
    """
    if options_set:
        return False

    def _check_zone(clue, zone, vertical):
        """ Look for lone singles in the zone (vertical or horizontal stack of squares) """
        cols_rows = CELLS_IN_COL if vertical else CELLS_IN_ROW
        with_clue = [cell for offset in range(3) for cell in cols_rows[3*zone + offset] if board[cell] == clue]
        if len(with_clue) == 2:
            squares = [zone + 3*offset if vertical else 3*zone + offset for offset in range(3)]
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
                    other_clue = [cell_id for cell_id in CELLS_IN_ROW[CELL_ROW[cell]] if board[cell_id] == clue]
                else:
                    other_clue = [cell_id for cell_id in CELLS_IN_COL[CELL_COL[cell]] if board[cell_id] == clue]
                if other_clue:
                    with_clue.append(other_clue[0])
                    greyed_out.append(cell)
                else:
                    clues.append(cell)
            if len(clues) == 1:
                _visual_elimination.clue_found = True
                board[clues[0]] = clue
                if window:
                    house = [cell for offset in range(3) for cell in cols_rows[3*zone + offset]]
                    window.draw_board(board, "visual_elimination", options_set=options_set,
                                      house=house, singles=with_clue, new_clue=clues[0], greyed_out=greyed_out)

    board_updated = False
    _visual_elimination.clue_found = True
    while _visual_elimination.clue_found:
        _visual_elimination.clue_found = False
        for clue in SUDOKU_VALUES_LIST:
            for zone in range(3):
                _check_zone(clue, zone, True)
            for zone in range(3):
                _check_zone(clue, zone, False)
        if _visual_elimination.clue_found:
            board_updated = True
    return board_updated


def _naked_singles(board, window, options_set=False):
    """ 'Naked Singles' technique (see: https://www.learn-sudoku.com/lone-singles.html) """
    if options_set:
        if not naked_singles:
            return False
        while naked_singles:
            naked_single = naked_singles.pop(0)
            clue = board[naked_single]
            to_remove = []
            for cell in ALL_NBRS[naked_single]:
                if clue in board[cell]:
                    to_remove.append((clue, cell))
                    board[cell] = board[cell].replace(clue, "")
                    if not board[cell]:
                        raise DeadEndException
                    elif len(board[cell]) == 1:
                        naked_singles.append(cell)
            if window:
                window.draw_board(board, "naked_singles", options_set=True, new_clue=naked_single,
                                  remove=to_remove, naked_singles=naked_singles)
        return True
    else:
        board_updated = False
        _naked_singles.clue_found = True
        while _naked_singles.clue_found:
            _naked_singles.clue_found = False
            for cell in range(81):
                if board[cell] == ".":
                    cell_opts = get_options(board, cell)
                    if len(cell_opts) == 1:
                        board[cell] = cell_opts.pop()
                        _naked_singles.clue_found = True
                        if window:
                            was_open_single = are_cells_set(board, CELLS_IN_ROW[CELL_ROW[cell]]) or \
                                              are_cells_set(board, CELLS_IN_COL[CELL_COL[cell]]) or \
                                              are_cells_set(board, CELLS_IN_SQR[CELL_SQR[cell]])
                            method = "open_singles" if was_open_single else "naked_singles"
                            window.draw_board(board, method, options_set=False,
                                              singles=[cell], new_clue=cell)
            if _naked_singles.clue_found:
                board_updated = True
        return board_updated


def _hidden_singles(board, window, options_set=False):
    """ 'Hidden Singles' technique (see: https://www.learn-sudoku.com/hidden-singles.html) """

    def _find_unique_positions(house):
        """ Find unique positions of missing clues within the house and 'solve' the cells """
        cell_solved = False
        while True:
            if not options_set:
                house_options = SUDOKU_VALUES_SET.copy()
                house_options -= set(''.join([board[cell_id] for cell_id in house]))
            else:
                house_options = set(''.join(board[cell_id] for cell_id in house if len(board[cell_id]) > 1))
            for option in house_options:
                in_cells = []
                greyed_out = []
                for cell in house:
                    if not options_set and board[cell] == ".":
                        cell_opts = SUDOKU_VALUES_SET.copy()
                        cell_opts -= set(''.join([board[cell_id] for cell_id in ALL_NBRS[cell]]))
                        if option in cell_opts:
                            in_cells.append(cell)
                        else:
                            greyed_out.append(cell)
                    if options_set and option in board[cell]:
                        in_cells.append(cell)

                if len(in_cells) == 1:
                    board[in_cells[0]] = option
                    cell_solved = True
                    if not options_set and window:
                        with_clue = set()
                        with_clue.add(in_cells[0])
                        window.draw_board(board, "hidden_pairs", options_set=False,
                                          singles=with_clue, new_clue=in_cells[0],
                                          house=house, greyed_out=greyed_out)
                    if options_set:
                        greyed_out = [(option, cell) for cell in ALL_NBRS[in_cells[0]] if option in board[cell]]
                        if window:
                            window.draw_board(board, "hidden_pairs", options_set=True,
                                              remove=greyed_out, singles=in_cells, house=house,
                                              naked_singles=naked_singles)
                    if options_set:
                        for value, cell_id in greyed_out:
                            board[cell_id] = board[cell_id].replace(value, "")
                            if len(board[cell_id]) == 1:
                                naked_singles.append(cell_id)
                    if window:
                        window.set_current_board(board)
                    _naked_singles(board, window, options_set)
                    break
            else:
                break

        return cell_solved      # TODO - should return True, None, False

    board_updated = False

    clue_found = True
    while clue_found:
        clue_found = False
        for row in range(9):
            if _find_unique_positions(CELLS_IN_ROW[row]):
                clue_found = True
        for col in range(9):
            if _find_unique_positions(CELLS_IN_COL[col]):
                clue_found = True
        for sqr in range(9):
            if _find_unique_positions(CELLS_IN_SQR[sqr]):
                clue_found = True
        if clue_found:
            board_updated = True

    return board_updated


def _hidden_pairs(board, window):
    """A Hidden Pair is basically just a “buried” Naked Pair.
    It occurs when two pencil marks appear in exactly two cells within
    the same house (row, column, or block).
    This technique doesn't solve any cells; instead it reveals Naked Pairs
    by removing other candidates in the Naked Pair cells
    (see https://www.learn-sudoku.com/hidden-pairs.html)
    """

    def _find_pairs(cells):
        values_dic = {}
        pairs_dic = {}
        to_remove = []
        pairs = []

        for cell in cells:
            for value in board[cell]:
                if value in values_dic:
                    values_dic[value].append(cell)
                else:
                    values_dic[value] = [cell]
        for value, in_cells in values_dic.items():
            if len(in_cells) == 2:
                pair = tuple(in_cells)
                if pair in pairs_dic:
                    pairs_dic[pair].append(value)
                else:
                    pairs_dic[pair] = [value]

        options_removed = False
        for in_cells, values in pairs_dic.items():
            if len(values) == 2:
                pair = ''.join(values)
                if len(board[in_cells[0]]) > 2:
                    board[in_cells[0]] = pair
                    options_removed = True
                if len(board[in_cells[1]]) > 2:
                    board[in_cells[1]] = pair
                    options_removed = True
                if options_removed:
                    pairs.append(in_cells[0])
                    pairs.append(in_cells[1])
                    other_options = [value for value in '123456789' if value not in pair]
                    for option in other_options:
                        to_remove.append((option, in_cells[0]))
                        to_remove.append((option, in_cells[1]))
                    if window:
                        window.draw_board(board, "hidden_pairs", remove=to_remove, subset=pairs, house=cells)
        return options_removed

    if window:
        window.display_info("'Hidden Pairs' technique:")
        window.set_current_board(board)

    pair_found = False
    board_updated = True
    while board_updated:
        board_updated = False
        for i in range(9):
            if _find_pairs(CELLS_IN_ROW[i]):
                board_updated = True
            if _find_pairs(CELLS_IN_COL[i]):
                board_updated = True
            if _find_pairs(CELLS_IN_SQR[i]):
                board_updated = True
            if board_updated:
                pair_found = True
    return pair_found


def _naked_twins(board, window):
    """For each 'house' (row, column or square) find twin cells with two options
    and remove the values from the list of candidates (options) of the remaining cells
    (see https://www.learn-sudoku.com/naked-pairs.html)
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
                    _naked_twins.board_updated = True
                    for value, cell in to_remove:
                        board[cell] = board[cell].replace(value, "")
                        if len(board[cell]) == 1:
                            naked_singles.append(cell)
                    if window:
                        window.draw_board(board, "naked_twins", remove=to_remove, subset=in_cells, house=cells,
                                          naked_singles=naked_singles)
                    if len(naked_singles) > 1:
                        print(f'\nnumber of nakked singles = {len(naked_singles)}')
                    _naked_singles(board, window, True)

    _naked_twins.board_updated = False
    if window:
        window.set_current_board(board)
    for i in range(9):
        _find_pairs(CELLS_IN_ROW[i])
        _find_pairs(CELLS_IN_COL[i])
        _find_pairs(CELLS_IN_SQR[i])
    return _naked_twins.board_updated


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
        else:
            _open_singles(board, window, options_set)
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

        return True
        # raise DeadEndException

