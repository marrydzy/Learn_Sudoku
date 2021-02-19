# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """


from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import is_clue, DeadEndException


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
            missing_value = SUDOKU_VALUES_SET.copy() - set(''.join([board[cell] for cell in house]))
            assert(len(missing_value) == 1)
            board[open_cells[0]] = missing_value.pop()
            if window:
                window.display_info("'Open Singles' technique:")
                window.draw_board(board, "manual_solution", singles=open_cells, new_clue=open_cells[0])
            return True
        return False

    board_updated = False

    clue_found = True
    while clue_found:
        clue_found = False
        for row in range(9):
            if _set_missing_number(CELLS_IN_ROW[row]):
                clue_found = True
        for col in range(9):
            if _set_missing_number(CELLS_IN_COL[col]):
                clue_found = True
        for sqr in range(9):
            if _set_missing_number(CELLS_IN_SQR[sqr]):
                clue_found = True
        if clue_found:
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
        with_clues = [cell for offset in range(3) for cell in cols_rows[3*zone + offset] if board[cell] == clue]
        if len(with_clues) == 2:
            squares = [zone + 3 * offset for offset in range(3)] if vertical else [3 * zone + offset for offset in
                                                                                   range(3)]
            squares.remove(CELL_SQR[with_clues[0]])
            squares.remove(CELL_SQR[with_clues[1]])
            cells = set(CELLS_IN_SQR[squares[0]])
            if vertical:
                cells -= set(CELLS_IN_COL[CELL_COL[with_clues[0]]]).union(set(CELLS_IN_COL[CELL_COL[with_clues[1]]]))
            else:
                cells -= set(CELLS_IN_ROW[CELL_ROW[with_clues[0]]]).union(set(CELLS_IN_ROW[CELL_ROW[with_clues[1]]]))
            possible_clue_cells = [cell for cell in cells if not is_clue(board[cell])]
            clues = []
            greyed_out = []
            for cell in possible_clue_cells:
                if vertical:
                    other_clue = [cell_id for cell_id in CELLS_IN_ROW[CELL_ROW[cell]] if board[cell_id] == clue]
                else:
                    other_clue = [cell_id for cell_id in CELLS_IN_COL[CELL_COL[cell]] if board[cell_id] == clue]
                if other_clue:
                    with_clues.append(other_clue[0])
                    greyed_out.append(cell)
                else:
                    clues.append(cell)
            if len(clues) == 1:
                board[clues[0]] = clue
                if window:
                    window.display_info("'Visual Elimination' technique:")
                    house = [cell for offset in range(3) for cell in cols_rows[3*zone + offset]]
                    window.draw_board(board, "manual_solution", house=house, singles=with_clues, new_clue=clues[0],
                                      greyed_out=greyed_out)
                return True
        return False

    board_updated = False

    clue_found = True
    while clue_found:
        clue_found = False
        for clue in SUDOKU_VALUES_LIST:
            for zone in range(3):
                if _check_zone(clue, zone, True):
                    clue_found = True
            for zone in range(3):
                if _check_zone(clue, zone, False):
                    clue_found = True
        if clue_found:
            board_updated = True

    return board_updated


def _naked_singles(board, window, options_set=False):
    """ 'Naked Singles' technique (see: https://www.learn-sudoku.com/lone-singles.html) """
    if options_set:
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
                window.display_info("'Naked Singles' technique:")
                window.draw_board(board, "hidden_pairs", new_clue=naked_single,
                                  remove=to_remove, naked_singles=naked_singles)
        return True
    else:
        def _solve_lone_singles():
            """ Find naked singles in the remaining cells without clue """
            fix_found = False
            for cell in range(81):
                if board[cell] == ".":
                    cell_opts = SUDOKU_VALUES_SET.copy()
                    cell_opts -= set(''.join([board[cell_id] for cell_id in ALL_NBRS[cell]]))
                    if len(cell_opts) == 1:
                        board[cell] = cell_opts.pop()
                        fix_found = True
                        if window:
                            window.display_info("'Naked Singles' technique:")
                            window.draw_board(board, "manual_solution", singles=[cell,], new_clue=cell)
            return fix_found

        board_updated = False
        while _solve_lone_singles():
            board_updated = True
        return board_updated


def _hidden_singles(board, window, options_set=False):
    """ 'Hidden Singles' technique (see: https://www.learn-sudoku.com/hidden-singles.html) """

    def _find_unique_positions(board, window, house):
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
                        window.display_info("'Hidden Singles' technique:")
                        window.draw_board(board, "manual_solution", singles=[in_cells[0], ], new_clue=in_cells[0],
                                          house=house, greyed_out=greyed_out)
                    if options_set and window:
                        greyed_out = [(option, cell) for cell in ALL_NBRS[in_cells[0]] if option in board[cell]]
                        window.display_info("'Hidden Singles' technique:")
                        window.draw_board(board, "hidden_pairs", remove=greyed_out, singles=in_cells, house=house,
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
            if _find_unique_positions(board, window, CELLS_IN_ROW[row]):
                clue_found = True
        for col in range(9):
            if _find_unique_positions(board, window, CELLS_IN_COL[col]):
                clue_found = True
        for sqr in range(9):
            if _find_unique_positions(board, window, CELLS_IN_SQR[sqr]):
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

    board_updated = True
    with_options = False
    while board_updated:
        board_updated = False
        if _open_singles(board, window):
            board_updated = True
        if _visual_elimination(board, window):
            board_updated = True
            continue
        if _naked_singles(board, window):
            board_updated = True
            continue
        if _hidden_singles(board, window):
            board_updated = True
            continue

    _init_options(board, window)
    board_updated = True
    while board_updated:
        board_updated = False
        if _hidden_singles(board, window, True):
            board_updated = True
        if _hidden_pairs(board, window):
            board_updated = True