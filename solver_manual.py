# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

import time
import itertools

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST, SUDOKU_VALUES_SET


def _check_zone(board, window, clue, zone, vertical):
    """ Look for lone singles in the zone (vertical or horizontal stack of squares) """
    cells = CELLS_IN_COL if vertical else CELLS_IN_ROW
    with_clues = [cell for offset in range(3) for cell in cells[3*zone + offset] if board[cell] == clue]
    if len(with_clues) == 2:
        squares = [zone + 3*offset for offset in range(3)] if vertical else [3*zone + offset for offset in range(3)]
        squares.remove(CELL_SQR[with_clues[0]])
        squares.remove(CELL_SQR[with_clues[1]])
        cells = set(CELLS_IN_SQR[squares[0]])
        if vertical:
            cells -= set(CELLS_IN_COL[CELL_COL[with_clues[0]]]).union(set(CELLS_IN_COL[CELL_COL[with_clues[1]]]))
        else:
            cells -= set(CELLS_IN_ROW[CELL_ROW[with_clues[0]]]).union(set(CELLS_IN_ROW[CELL_ROW[with_clues[1]]]))
        possible_clue_cells = [cell for cell in cells if board[cell] == '.']
        clues = []
        for cell in possible_clue_cells:
            if vertical:
                other_clue = [cell_id for cell_id in CELLS_IN_ROW[CELL_ROW[cell]] if board[cell_id] == clue]
            else:
                other_clue = [cell_id for cell_id in CELLS_IN_COL[CELL_COL[cell]] if board[cell_id] == clue]
            if other_clue:
                with_clues.append(other_clue[0])
            else:
                clues.append(cell)
        if len(clues) == 1:
            board[clues[0]] = clue
            if window:
                window.draw_board(board, "manual_solution", singles=with_clues, new_clue=clues[0])
            return True
    return False


def _find_naked_singles(board, window):
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
                    window.draw_board(board, "manual_solution", singles=[cell,], new_clue=cell)
    return board_updated


def _find_unique_positions(board, window, house):
    """ Find unique positions of missing clues within the house """
    board_updated = False
    house_options = SUDOKU_VALUES_SET.copy()
    house_options -= set(''.join([board[cell_id] for cell_id in house]))
    for option in house_options:
        in_cells = []
        for cell in house:
            if board[cell] == ".":
                cell_opts = SUDOKU_VALUES_SET.copy()
                cell_opts -= set(''.join([board[cell_id] for cell_id in ALL_NBRS[cell]]))
                if option in  cell_opts:
                    in_cells.append(cell)
        if len(in_cells) == 1:
            board[in_cells[0]] = option
            board_updated = True
            if window:
                window.draw_board(board, "manual_solution", singles=[in_cells[0], ], new_clue=in_cells[0])
    return board_updated


def manual_solver(board, window, _):
    """ TODO - manual solver """

    board_updated = True
    while board_updated:
        board_updated = False
        for clue in SUDOKU_VALUES_LIST:
            for zone in range(3):
                if _check_zone(board, window, clue, zone, True):
                    board_updated = True
            for zone in range(3):
                if _check_zone(board, window, clue, zone, False):
                    board_updated = True

    # TODO - check if solved
    board_updated = True
    while board_updated:
        board_updated = _find_naked_singles(board, window)

    # TODO - check if solved
    board_updated = True
    while board_updated:
        board_updated = False
        for row in range(9):
            if _find_unique_positions(board, window, CELLS_IN_ROW[row]):
                board_updated = True
        for col in range(9):
            if _find_unique_positions(board, window, CELLS_IN_COL[col]):
                board_updated = True
        for sqr in range(9):
            if _find_unique_positions(board, window, CELLS_IN_SQR[sqr]):
                board_updated = True
