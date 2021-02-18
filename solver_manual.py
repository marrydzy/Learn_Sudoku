# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """


from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET
from utils import is_clue


def _open_singles(board, window):
    """ 'Open Singles' technique (see: https://www.learn-sudoku.com/open-singles.html) """

    def _set_missing_number(board, window, house):
        open_cells = [cell for cell in house if not is_clue(board[cell])]
        if len(open_cells) == 1:
            missing_value = SUDOKU_VALUES_SET.copy() - set(''.join([board[cell] for cell in house]))
            board[open_cells[0]] = missing_value.pop()
            print("\nOpen Singles")
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
            if _set_missing_number(board, window, CELLS_IN_ROW[row]):
                clue_found = True
        for col in range(9):
            if _set_missing_number(board, window, CELLS_IN_COL[col]):
                clue_found = True
        for sqr in range(9):
            if _set_missing_number(board, window, CELLS_IN_SQR[sqr]):
                clue_found = True
        if clue_found:
            board_updated = True
            
    return board_updated


def _visual_elimination(board, window):
    """ 'Visual Elimination' techniques (see: https://www.learn-sudoku.com/visual-elimination.html) """

    def _check_zone(board, window, clue, zone, vertical):
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
                if _check_zone(board, window, clue, zone, True):
                    clue_found = True
            for zone in range(3):
                if _check_zone(board, window, clue, zone, False):
                    clue_found = True
        if clue_found:
            board_updated = True

    return board_updated


def _naked_singles(board, window):
    """ 'Naked Singles' technique (see: https://www.learn-sudoku.com/lone-singles.html) """

    def _solve_lone_singles(board, window):
        """ Find naked singles in the remaining cells without clue """
        board_updated = False
        for cell in range(81):
            if board[cell] == ".":
                cell_opts = SUDOKU_VALUES_SET.copy()
                cell_opts -= set(''.join([board[cell_id] for cell_id in ALL_NBRS[cell]]))
                if len(cell_opts) == 1:
                    board[cell] = cell_opts.pop()
                    board_updated = True
                    if window:
                        window.display_info("'Naked Singles' technique:")
                        window.draw_board(board, "manual_solution", singles=[cell,], new_clue=cell)
        return board_updated

    board_updated = False

    clue_found = True
    while clue_found:
        clue_found = _solve_lone_singles(board, window)
        if clue_found:
            board_updated = True

    return board_updated


def _hidden_singles(board, window):
    """ 'Hidden Singles' technique (see: https://www.learn-sudoku.com/hidden-singles.html) """

    def _find_unique_positions(board, window, house):
        """ Find unique positions of missing clues within the house """
        board_updated = False
        house_options = SUDOKU_VALUES_SET.copy()
        house_options -= set(''.join([board[cell_id] for cell_id in house]))
        for option in house_options:
            in_cells = []
            greyed_out = []
            for cell in house:
                if board[cell] == ".":
                    cell_opts = SUDOKU_VALUES_SET.copy()
                    cell_opts -= set(''.join([board[cell_id] for cell_id in ALL_NBRS[cell]]))
                    if option in  cell_opts:
                        in_cells.append(cell)
                    else:
                        greyed_out.append((cell))
            if len(in_cells) == 1:
                board[in_cells[0]] = option
                board_updated = True
                if window:
                    window.display_info("'Hidden Singles' technique:")
                    window.draw_board(board, "manual_solution", singles=[in_cells[0], ], new_clue=in_cells[0],
                                      house=house, greyed_out=greyed_out)
        return board_updated

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
    while board_updated:
        board_updated = False
        if _open_singles(board, window):
            board_updated = True
        if _visual_elimination(board, window):
            board_updated = True
        if _naked_singles(board, window):
            board_updated = True
        if _hidden_singles(board, window):
            board_updated = True

    _init_options(board, window)