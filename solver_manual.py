# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from collections import defaultdict, namedtuple

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_BOX
from utils import ALL_NBRS
from utils import is_clue, is_solved, set_cell_options, set_neighbours_options
from utils import get_stats

import singles
import intersections
import subsets
import uniqueness_tests
import intermediate_techniques
import fish
import wings
import coloring
import almost_locked_set
import questionable

board_image_stack = []
iter_stack = []
solver_status_stack = []

Strategy = namedtuple("strategy", ["name", "callable"])

solver_strategies = [
    Strategy("full_house", True),
    Strategy("visual_elimination", True),
    Strategy("naked_singles", True),
    Strategy("hidden_singles", True),
    Strategy("locked_candidates", True),
    Strategy("locked_candidates_type_1", False),
    Strategy("locked_candidates_type_2", False),
    Strategy("naked_pair", True),
    Strategy("hidden_pair", True),
    Strategy("swordfish", True),
    Strategy("xy_wing", True),
    Strategy("xyz_wing", True),
    Strategy("wxyz_wing", True),
    Strategy("w_wing", True),
    Strategy("naked_triplet", True),
    Strategy("test_1", True),
    Strategy("test_2", True),
    Strategy("test_3", True),
    Strategy("test_4", True),
    Strategy("test_5", True),
    Strategy("test_6", True),
    Strategy("skyscraper", True),
    Strategy("x_wing", True),
    Strategy("jellyfish", True),
    Strategy("finned_x_wing", True),
    Strategy("finned_swordfish", True),
    Strategy("finned_jellyfish", True),
    Strategy("finned_squirmbag", True),
    Strategy("finned_mutant_x_wing", True),
    Strategy("simple_colors", True),
    Strategy("multi_colors", True),
    Strategy("x_colors", True),
    Strategy("three_d_medusa", True),
    Strategy("naked_xy_chain", True),
    Strategy("hidden_xy_chain", True),
    Strategy("empty_rectangle", True),
    Strategy("sue_de_coq", True),
    Strategy("als_xy", True),
    Strategy("als_xz", True),
    Strategy("death_blossom", True),
    Strategy("als_xy_wing", True),
    Strategy("hidden_triplet", True),
    Strategy("squirmbag", True),
    Strategy("naked_quad", True),
    Strategy("hidden_quad", True),
    Strategy("almost_locked_candidates", True),
    Strategy("franken_x_wing", True),
]


solver_methods = {
    "full_house": singles.full_house,
    "visual_elimination": singles.visual_elimination,
    "naked_singles": singles.naked_singles,
    "hidden_singles": singles.hidden_singles,
    "locked_candidates": intersections.locked_candidates,
    "naked_pair": subsets.naked_pair,
    "hidden_pair": subsets.hidden_pair,
    "swordfish": fish.swordfish,
    "xy_wing": wings.xy_wing,
    "xyz_wing": wings.xyz_wing,
    "wxyz_wing": wings.wxyz_wing,
    "w_wing": wings.w_wing,
    "naked_triplet": subsets.naked_triplet,
    "test_1": uniqueness_tests.test_1,
    "test_2": uniqueness_tests.test_2,
    "test_3": uniqueness_tests.test_3,
    "test_4": uniqueness_tests.test_4,
    "test_5": uniqueness_tests.test_5,
    "test_6": uniqueness_tests.test_6,
    "skyscraper": intermediate_techniques.skyscraper,
    "x_wing": fish.x_wing,
    "jellyfish": fish.jellyfish,
    "finned_x_wing": fish.finned_x_wing,
    "finned_swordfish": fish.finned_swordfish,
    "finned_jellyfish": fish.finned_jellyfish,
    "finned_squirmbag": fish.finned_squirmbag,
    "finned_mutant_x_wing": wings.finned_mutant_x_wing,
    "simple_colors": coloring.simple_colors,
    "multi_colors": coloring.multi_colors,
    "x_colors": coloring.x_colors,
    "three_d_medusa": coloring.three_d_medusa,
    "naked_xy_chain": coloring.naked_xy_chain,
    "hidden_xy_chain": coloring.hidden_xy_chain,
    "empty_rectangle": intermediate_techniques.empty_rectangle,
    "sue_de_coq": intermediate_techniques.sue_de_coq,
    "als_xy": almost_locked_set.als_xy,
    "als_xz": almost_locked_set.als_xz,
    "death_blossom": almost_locked_set.death_blossom,
    "als_xy_wing": almost_locked_set.als_xy_wing,
    "hidden_triplet": subsets.hidden_triplet,
    "squirmbag": fish.squirmbag,
    "naked_quad": subsets.naked_quad,
    "hidden_quad":subsets.hidden_quad,
    "almost_locked_candidates": questionable.almost_locked_candidates,
    "franken_x_wing": questionable.franken_x_wing,

}


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
        self.clues_found_baseline = set()
        self.options_visible_baseline = set()
        self.conflicted_cells = set()

    def initialize(self, board):
        self.clues_defined = set(cell_id for cell_id in range(81) if board[cell_id] != ".")
        self.reset(board)

    def capture_baseline(self, board, window):
        if window and window.show_solution_steps:
            self.board_baseline = board.copy()
            self.naked_singles_baseline = self.naked_singles.copy()
            self.clues_found_baseline = self.clues_found.copy()
            self.options_visible_baseline = window.options_visible.copy()

    def restore_baseline(self, board, window):
        for cell_id in range(81):
            board[cell_id] = self.board_baseline[cell_id]
        self.naked_singles = self.naked_singles_baseline.copy()
        self.clues_found = self.clues_found_baseline.copy()
        window.options_visible = self.options_visible_baseline.copy()

    def restore(self, solver_status_baseline):
        self.options_set = solver_status_baseline.options_set
        self.clues_defined = solver_status_baseline.clues_defined.copy()
        self.clues_found = solver_status_baseline.clues_found.copy()
        self.naked_singles = solver_status_baseline.naked_singles.copy()
        self.board_baseline = solver_status_baseline.board_baseline.copy()
        self.naked_singles_baseline = solver_status_baseline.naked_singles_baseline.copy()
        self.clues_found_baseline = solver_status_baseline.clues_found_baseline.copy()
        self.options_visible_baseline = solver_status_baseline.options_visible_baseline.copy()
        self.conflicted_cells = solver_status_baseline.conflicted_cells.copy()

    def reset(self, board):
        self.options_set = False
        self.clues_found.clear()
        self.naked_singles.clear()
        self.naked_singles_baseline.clear()
        self.clues_found_baseline.clear()
        self.options_visible_baseline.clear()
        for cell_id in range(81):
            if cell_id not in self.clues_defined:
                board[cell_id] = "."
        self.board_baseline = board.copy()


solver_status = SolverStatus()


def _the_same_as_clue_found(board, window, options_set):
    """ Entered key is the same as clicked cell value """
    cell_id, value, as_clue = window.clue_entered
    solver_status.clues_found.remove(cell_id)
    if as_clue:
        if options_set:
            set_cell_options(cell_id, board, solver_status)
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
                set_cell_options(cell_id, board, solver_status)
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
            if is_clue(cell, board, solver_status):
                values_dict[board[cell]].append(cell)
        for value, in_cells in values_dict.items():
            if len(in_cells) > 1:
                solver_status.conflicted_cells.extend(in_cells)

    solver_status.conflicted_cells.clear()
    for i in range(9):
        _check_house(CELLS_IN_ROW[i])
        _check_house(CELLS_IN_COL[i])
        _check_house(CELLS_IN_BOX[i])
    solver_status.conflicted_cells = list(set(solver_status.conflicted_cells))

    if window.solved_board:
        window.wrong_values.clear()
        for cell_id in range(81):
            if cell_id not in solver_status.clues_defined:
                if cell_id in solver_status.clues_found:
                    if board[cell_id] != window.solved_board[cell_id]:
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
    if is_solved(board, solver_status) and window.solver_loop != -1:
        kwargs["solver_tool"] = "end_of_game"
    return kwargs


def _clear_stacks(board):
    """ Clear stacks used by apply_brute_force()
    TODO - this is a temporary solution!
    """
    if board_image_stack and is_solved(board, solver_status):
        board_image_stack.clear()
        iter_stack.clear()
        solver_status_stack.clear()


strategies_failure_counter = 0     # TODO - for debugging/testing only!


@get_stats
def manual_solver(board, window, count_strategies_failures):
    """ Main solver loop:
     - The algorithm draws current board and waits until a predefined event happens
     - Each 'technique' function returns kwargs dictionary if the board is updated, empty dictionary otherwise
     - Interactive vs. step-wise execution is controlled by 'window.calculate_next_clue' parameter """

    global strategies_failure_counter  # TODO - for debugging/testing only!

    kwargs = {"solver_tool": "plain_board"}
    while True:
        if window:
            _clear_stacks(board)
            window.draw_board(board, **kwargs)
            kwargs = _set_manually(board, window)
            if kwargs:
                continue
            if not window.calculate_next_clue:
                continue
            elif window.show_solution_steps:
                window.calculate_next_clue = False

        if is_solved(board, solver_status):
            return True
        for strategy in solver_strategies:
            if strategy.callable:
                kwargs = solver_methods[strategy.name](solver_status, board, window)
                if kwargs:
                    if window and window.suggest_technique:
                        solver_status.restore_baseline(board, window)
                    break
        else:
            if not is_solved(board, solver_status):        # TODO: for debugging only!
                if count_strategies_failures:
                    strategies_failure_counter += 1
                    # print(f"\n{strategies_failure_counter = }")
                    pass
            return False
    return True
