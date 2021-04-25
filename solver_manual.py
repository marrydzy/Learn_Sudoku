# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

# import itertools
from collections import defaultdict

# from icecream import ic

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_SQR
from utils import ALL_NBRS
from utils import is_clue, is_solved, set_cell_options, set_neighbours_options

import basic_techniques
import advanced_techniques

# from utils import get_pairs


class SolverStatus:
    """ class to store data needed for recovering of puzzle
    status prior to applying a method """
    def __init__(self):
        self.options_set = False
        self.clues_defined = set()
        self.clues_found = set()
        self.naked_singles = set()
        self.board_baseline = list()
        self.naked_singles_baseline = set()
        self.clues_found_baseline = []
        self.options_visible_baseline = set()
        self.conflicted_cells = []

    def initialize(self, board, window):
        self.clues_defined = set(cell_id for cell_id in range(81) if board[cell_id] != ".")
        self.reset(board, window)

    def capture_baseline(self, board, window):
        if window and window.show_solution_steps and not window.animate:
            window.set_current_board(board)
            self.naked_singles_baseline = self.naked_singles.copy()
            self.clues_found_baseline = self.clues_found.copy()
            self.options_visible_baseline = window.options_visible.copy()

    def restore_baseline(self, board, window):
        self.naked_singles = self.naked_singles_baseline.copy()
        self.clues_found = self.clues_found_baseline.copy()
        if window:
            window.options_visible = self.options_visible_baseline.copy()
            for cell_id in range(81):
                board[cell_id] = self.board_baseline[cell_id]

    def reset(self, board, window):
        self.options_set = False
        self.clues_found.clear()
        self.naked_singles.clear()
        self.naked_singles_baseline.clear()
        self.clues_found_baseline.clear()
        self.options_visible_baseline.clear()
        if window:
            for cell_id in range(81):
                if cell_id not in self.clues_defined:
                    board[cell_id] = "."
            window.set_current_board(board)


solver_status = SolverStatus()


def _the_same_as_clue_found(board, window, options_set):
    """ Entered key is the same as clicked cell value """
    cell_id, value, as_clue = window.clue_entered
    solver_status.clues_found.remove(cell_id)
    if as_clue:
        if options_set:
            set_cell_options(cell_id, board, window, solver_status)
        else:
            board[cell_id] = "."
    else:
        window.options_visible.add(cell_id)
        solver_status.naked_singles.add(cell_id)
    if options_set:
        set_neighbours_options(cell_id, board, window, solver_status)


def _other_than_clue_found(board, window, options_set):
    """ Entered key other than clicked cell value """
    cell_id, value, as_clue = window.clue_entered
    if cell_id in solver_status.naked_singles:
        solver_status.naked_singles.remove(cell_id)
    board[cell_id] = value
    if as_clue:
        solver_status.clues_found.add(cell_id)
    else:
        solver_status.clues_found.remove(cell_id)
        solver_status.naked_singles.add(cell_id)
        window.options_visible.add(cell_id)
    if options_set:
        set_neighbours_options(cell_id, board, window, solver_status)


def _as_clue_and_undefined(board, window, options_set):
    """ Entering clue in undefined cell """
    cell_id, value, as_clue = window.clue_entered
    if cell_id in window.options_visible:
        window.options_visible.remove(cell_id)
    if cell_id in solver_status.naked_singles:
        solver_status.naked_singles.remove(cell_id)
    board[cell_id] = value
    solver_status.clues_found.add(cell_id)
    if options_set:
        set_neighbours_options(cell_id, board, window, solver_status)


def _as_opt_and_undefined(board, window):
    """ Entering an option in undefined cell """
    cell_id, value, as_clue = window.clue_entered
    if cell_id in window.options_visible:
        if cell_id in solver_status.naked_singles:
            solver_status.naked_singles.remove(cell_id)
        if value in board[cell_id]:
            board[cell_id] = board[cell_id].replace(value, "")
            if len(board[cell_id]) == 0:
                set_cell_options(cell_id, board, window, solver_status)
                window.options_visible.remove(cell_id)
            elif len(board[cell_id]) == 1:
                solver_status.naked_singles.add(cell_id)
        else:
            board[cell_id] += value
    else:
        board[cell_id] = value
        window.options_visible.add(cell_id)
        solver_status.naked_singles.add(cell_id)


def _check_board_integrity(board, window):
    """ Check integrity of the current board:
     - check for conflicted cells in each row, column and box
     - if solved board is defined, check entered values (clues or options) if correct
    """

    def _check_house(cells):
        values_dict = defaultdict(list)
        for cell in cells:
            if is_clue(cell, board, window):
                values_dict[board[cell]].append(cell)
        for value, in_cells in values_dict.items():
            if len(in_cells) > 1:
                solver_status.conflicted_cells.extend(in_cells)

    solver_status.conflicted_cells.clear()
    for i in range(9):
        _check_house(CELLS_IN_ROW[i])
        _check_house(CELLS_IN_COL[i])
        _check_house(CELLS_IN_SQR[i])
    solver_status.conflicted_cells = list(set(solver_status.conflicted_cells))

    if window.solved_board:
        window.wrong_values.clear()
        for cell_id in range(81):
            if cell_id not in solver_status.clues_defined:
                if cell_id in solver_status.clues_found:
                    if board[cell_id] != window.solved_board[cell_id]:
                        window.wrong_values.add(cell_id)
                elif cell_id in window.options_visible:
                    if window.solved_board[cell_id] not in set(board[cell_id]):
                        window.wrong_values.add(cell_id)


def _set_manually(board, window):
    """ Interactively take entered values """
    kwargs = {}
    if window and window.clue_entered[0] is not None:
        solver_status.capture_baseline(board, window)
        cell_id, value, as_clue = window.clue_entered
        if cell_id in solver_status.clues_found:
            if board[cell_id] == value:
                _the_same_as_clue_found(board, window, solver_status.options_set)
            else:
                _other_than_clue_found(board, window, solver_status.options_set)
        else:
            if as_clue:
                _as_clue_and_undefined(board, window, solver_status.options_set)
            else:
                _as_opt_and_undefined(board, window)
        _check_board_integrity(board, window)
        window.clue_entered = (None, None, None)
        cell_house = ALL_NBRS[solver_status.conflicted_cells[-1]] if solver_status.conflicted_cells else list()
        kwargs = {"solver_tool": "plain_board",
                  "wrong_values": window.wrong_values,
                  "conflicted_cells": solver_status.conflicted_cells,
                  "cell_house": cell_house,
                  }
    if is_solved(board, window) and window.solver_loop != -1:
        kwargs["solver_tool"] = "end_of_game"
    return kwargs


def manual_solver(board, window):
    """ Main solver loop:
     - The algorithm draws current board and waits until a predefined event happens
     - Each '_method' function returns True if the board is updated, False otherwise
     - Interactive vs. step-wise execution is controlled by 'window.calculate_next_clue' parameter """

    solver_status.initialize(board, window)
    kwargs = {"solver_tool": "plain_board"}
    while True:
        if window:
            window.draw_board(board, **kwargs)
            kwargs = _set_manually(board, window)
            if kwargs:
                continue
            if not window.calculate_next_clue:
                continue
            elif window.show_solution_steps:
                window.calculate_next_clue = False

        kwargs = basic_techniques.open_singles(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.visual_elimination(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.naked_singles(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.hidden_singles(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.naked_twins(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.hidden_pair(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.naked_triplets(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.hidden_triplet(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.naked_quads(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.hidden_quad(solver_status, board, window)
        if kwargs:
            continue
        kwargs = basic_techniques.omissions(solver_status, board, window)
        if kwargs:
            continue
        kwargs = advanced_techniques.unique_rectangles(solver_status, board, window)
        if kwargs:
            continue
        kwargs = advanced_techniques.x_wings(solver_status, board, window)
        if kwargs:
            continue
        kwargs = advanced_techniques.finned_x_wing(solver_status, board, window)
        if kwargs:
            continue
        kwargs = advanced_techniques.y_wings(solver_status, board, window)
        if kwargs:
            continue
        kwargs = advanced_techniques.swordfish(solver_status, board, window)
        if kwargs:
            continue

        if not is_solved(board, window):        # TODO: for debugging only!
            pass
            # print('\nLeaving manual_solver')
        return False
