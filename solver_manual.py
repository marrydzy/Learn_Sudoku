# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from collections import defaultdict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import is_clue, is_solved, is_single, get_options, are_cells_set, DeadEndException

naked_singles = []


def _remove_options(board, to_remove):
    """ utility function: removes options as per 'to_remove' list """
    for option, cell in to_remove:
        board[cell] = board[cell].replace(option, "")
        if not board[cell]:
            raise DeadEndException
        elif len(board[cell]) == 1:
            naked_singles.append(cell)


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
                    window.draw_board(board, "visual_elimination", options_set=options_set,
                                      house=house, singles=with_clue, new_clue=clues[0], greyed_out=greyed_out)
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
            if window:
                window.draw_board(board, "naked_singles", options_set=True, new_clue=naked_single,
                                  remove=to_remove, naked_singles=naked_singles)
        return True
    else:
        for cell in range(81):
            if board[cell] == ".":
                cell_opts = get_options(board, cell)
                if len(cell_opts) == 1:
                    board[cell] = cell_opts.pop()
                    if window:
                        window.draw_board(board, "naked_singles", options_set=False,
                                          singles=[cell], new_clue=cell)
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
                if window:
                    window.set_current_board(board)     # to properly display the hidden single
                if options_set:
                    to_remove = [(option, cell) for cell in ALL_NBRS[in_cells[0]] if option in board[cell]]
                    _remove_options(board, to_remove)
                if window:
                    window.draw_board(board, "hidden_singles", options_set=options_set, singles=[in_cells[0]],
                                      new_clue=in_cells[0], house=house, greyed_out=greyed_out)
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
                cell_1, cell_2 = in_cells
                if len(board[cell_1]) > 2 or len(board[cell_2]) > 2:
                    board[cell_1] = pair
                    board[cell_2] = pair
                    other_options = [value for value in '123456789' if value not in pair]
                    to_remove = []
                    for option in other_options:
                        to_remove.append((option, cell_1))
                        to_remove.append((option, cell_2))
                    if window:
                        window.draw_board(board, "hidden_pairs", remove=to_remove,
                                          subset=[cell_1, cell_2], house=cells)
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
                    # if len(naked_singles) > 1:    TODO
                        # print(f'\nnumber of nakked singles = {len(naked_singles)}')
                    _naked_singles(board, window, True)

    _naked_twins.board_updated = False
    if window:
        window.set_current_board(board)
    for i in range(9):
        _find_pairs(CELLS_IN_ROW[i])
        _find_pairs(CELLS_IN_COL[i])
        _find_pairs(CELLS_IN_SQR[i])
    return _naked_twins.board_updated


def _omissions(board, window):
    """For rows and columns:
     - when pencil marks in a row or column are contained within a single block,
       the pencil marks elsewhere in the block can be removed
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
                in_blocks = set(CELL_SQR[cell] for cell in unsolved if value in board[cell])
                if len(in_blocks) == 1:
                    # single = is_single(board, cells, value)
                    # if single is not None:
                    #     print(f'{single = }  {board[single] = }')
                    #     board[single] = value
                    #     naked_singles.append(single)
                        # if window:
                            # window.set_current_board(board)
                     #   _naked_singles(board, window, True)
                    # else:
                    other_cells = set(CELLS_IN_SQR[in_blocks.pop()]) - set(cells)
                    to_remove = [(value, cell) for cell in other_cells if value in board[cell]]
                    if to_remove:
                        _remove_options(to_remove, cells, other_cells)

    def _in_block(cells):
        options = SUDOKU_VALUES_SET - {board[cell] for cell in cells if len(board[cell]) == 1}
        if options:
            for value in options:
                unsolved = {cell for cell in cells if len(board[cell]) > 1}
                in_rows = set(CELL_ROW[cell] for cell in unsolved if value in board[cell])
                in_cols = set(CELL_COL[cell] for cell in unsolved if value in board[cell])
                if len(in_rows) == 1 and len(in_cols) == 1:
                    single = is_single(board, cells, value)
                    board[single] = value
                    naked_singles.append(single)
                    if window:
                        window.set_current_board(board)
                    _naked_singles(board, window, True)
                else:
                    other_cells = set()
                    if len(in_rows) == 1:
                        other_cells = set(CELLS_IN_ROW[in_rows.pop()]) - set(cells)
                    elif len(in_cols) == 1:
                        other_cells = set(CELLS_IN_COL[in_cols.pop()]) - set(cells)
                    to_remove = [(value, cell) for cell in other_cells if value in board[cell]]
                    if to_remove:
                        _remove_options(to_remove, cells, other_cells)

    def _remove_options(to_remove, house, other_cells):
        _omissions.board_updated = True
        for value, cell in to_remove:
            board[cell] = board[cell].replace(value, "")
            if not board[cell]:
                raise DeadEndException
            elif len(board[cell]) == 1:
                naked_singles.append(cell)
        if window:
            claims = [(to_remove[0][0], cell) for cell in house]
            window.draw_board(board, "omissions", claims=claims, remove=to_remove,
                              singles=naked_singles, house=house, other_cells=other_cells)
        if naked_singles:
            _naked_singles(board, window, True)

    board_updated = False
    while True:
        _omissions.board_updated = False
        for i in range(9):
            _in_row_col(CELLS_IN_ROW[i])
            _in_row_col(CELLS_IN_COL[i])
            _in_block(CELLS_IN_SQR[i])
        if _omissions.board_updated:
            board_updated = True
        else:
            break
    return board_updated


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
            _naked_twins(board, window)
            continue
        if _naked_twins(board, window):
            continue
        if _omissions(board, window):
            continue

        return True
        # raise DeadEndException

