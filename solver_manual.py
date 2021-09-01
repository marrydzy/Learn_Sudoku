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

Strategy = namedtuple("Strategy", ["solver", "technique", "name", "priority", "rating", "active"])

solver_strategies = {
    "full_house": Strategy(singles.full_house, "singles", "Full House", 1, 4, True),
    "visual_elimination": Strategy(singles.visual_elimination, "singles", "Visual Elimination", 2, 4, True),
    "naked_singles": Strategy(singles.naked_singles, "singles", "Naked Single", 3, 4, True),
    "hidden_singles": Strategy(singles.hidden_singles, "singles", "Hidden Single", 4, 14, True),
    "locked_candidates": Strategy(intersections.locked_candidates, "intersections", "Locked Candidates", 5, 50, True),
    "locked_candidates_type_1": Strategy(None, "", "Locked Candidates - Type 1 (Pointing)", 999, 0, False),
    "locked_candidates_type_2": Strategy(None, "", "Locked Candidates - Type 2 (Claiming)", 999, 0, False),
    "naked_pair": Strategy(subsets.naked_pair, "subsets", "Naked Pair", 6, 60, True),
    "hidden_pair": Strategy(subsets.hidden_pair, "subsets", "Hidden Pair", 7, 70, True),
    "swordfish": Strategy(fish.swordfish, "fish", "Swordfish", 8, 140, True),
    "xy_wing": Strategy(wings.xy_wing, "wings", "XY-Wing", 9, 160, True),
    "xyz_wing": Strategy(wings.xyz_wing, "wings", "XYZ-Wing", 10, 180, True),
    "wxyz_wing": Strategy(wings.wxyz_wing, "wings", "WXYZ-Wing", 11, 240, True),
    "wxyz_wing_type_1": Strategy(None, "", "WXYZ-Wing (Type 1)", 999, 0, False),
    "wxyz_wing_type_2": Strategy(None, "", "WXYZ-Wing (Type 2)", 999, 0, False),
    "wxyz_wing_type_3": Strategy(None, "", "WXYZ-Wing (Type 3)", 999, 0, False),
    "wxyz_wing_type_4": Strategy(None, "", "WXYZ-Wing (Type 4)", 999, 0, False),
    "wxyz_wing_type_5": Strategy(None, "", "WXYZ-Wing (Type 5)", 999, 0, False),
    "w_wing": Strategy(wings.w_wing, "wings", "W-Wing", 12, 150, True),
    "naked_triplet": Strategy(subsets.naked_triplet, "subsets", "Naked Triplet", 13, 80, True),
    "test_1": Strategy(uniqueness_tests.test_1, "uniqueness_tests", "Uniqueness Test 1", 14, 100, True),
    "test_2": Strategy(uniqueness_tests.test_2, "uniqueness_tests", "Uniqueness Test 2", 15, 100, True),
    "test_3": Strategy(uniqueness_tests.test_3, "uniqueness_tests", "Uniqueness Test 3", 16, 100, True),
    "test_4": Strategy(uniqueness_tests.test_4, "uniqueness_tests", "Uniqueness Test 4", 17, 100, True),
    "test_5": Strategy(uniqueness_tests.test_5, "uniqueness_tests", "Uniqueness Test 5", 18, 100, True),
    "test_6": Strategy(uniqueness_tests.test_6, "uniqueness_tests", "Uniqueness Test 6", 19, 100, True),
    "skyscraper": Strategy(intermediate_techniques.skyscraper, "Single Digit Patterns", "Skyscraper", 20, 130, True),
    "x_wing": Strategy(fish.x_wing, "fish", "X-Wing", 21, 100, True),
    "jellyfish": Strategy(fish.jellyfish, "fish", "Jellyfish", 22, 470, True),
    "finned_x_wing": Strategy(fish.finned_x_wing, "fish", "Finned X-Wing", 23, 130, True),
    "finned_swordfish": Strategy(fish.finned_swordfish, "fish", "Finned Swordfish", 24, 200, True),
    "finned_jellyfish": Strategy(fish.finned_jellyfish, "fish", "Finned Jellyfish", 25, 240, True),
    "finned_squirmbag": Strategy(fish.finned_squirmbag, "fish", "Finned Squirmbag", 26, 470, True),
    "finned_mutant_x_wing": Strategy(wings.finned_mutant_x_wing, "wings", "Finned Mutant X-Wing", 27, 470, True),
    "finned_rccb_mutant_x_wing": Strategy(None, "", "Finned RCCB Mutant X-Wing", 999, 0, False),
    "finned_rbcc_mutant_x_wing": Strategy(None, "", "Finned RBCC Mutant X-Wing", 999, 0, False),
    "finned_cbrc_mutant_x_wing": Strategy(None, "", "Finned CBRC Mutant X-Wing", 999, 0, False),
    "simple_colors": Strategy(coloring.simple_colors, "coloring", "Simple Colors", 28, 150, True),
    "color_trap": Strategy(None, "", "Simple Colors - Color Trap", 999, 0, False),
    "color_wrap": Strategy(None, "", "Simple Colors - Color Wrap", 999, 0, False),
    "multi_colors": Strategy(coloring.multi_colors, "coloring", "Multi-Colors", 29, 200, True),
    "multi_colors-color_wrap": Strategy(None, "", "Multi-Colors - Color Wrap", 999, 0, False),
    "multi_colors-color_wing": Strategy(None, "", "Multi-Colors - Color Wing", 999, 0, False),
    "x_colors": Strategy(coloring.x_colors, "coloring", "X-Colors", 30, 200, True),
    "x_colors_elimination": Strategy(None, "", "X-Colors - Elimination", 999, 0, False),
    "x_colors_contradiction": Strategy(None, "", "X-Colors - Contradiction", 999, 0, False),
    "three_d_medusa": Strategy(coloring.three_d_medusa, "coloring", "3D Medusa", 31, 320, True),
    "naked_xy_chain": Strategy(coloring.naked_xy_chain, "coloring", "Naked XY Chain", 32, 310, True),
    "hidden_xy_chain": Strategy(coloring.hidden_xy_chain, "coloring", "Hidden XY Chain", 33, 310, True),
    "empty_rectangle": Strategy(intermediate_techniques.empty_rectangle, "intermediate_techniques",
                                "Epmpty Rectangle", 34, 130, True),
    "sue_de_coq": Strategy(intermediate_techniques.sue_de_coq, "intermediate_techniques", "Sue de Coq' technique",
                           35, 130, True),
    "als_xy": Strategy(almost_locked_set.als_xy, "almost_locked_set", "ALS-XY", 35, 320, True),
    "als_xz": Strategy(almost_locked_set.als_xz, "almost_locked_set", "ALS-XZ", 36, 300, True),
    "death_blossom": Strategy(almost_locked_set.death_blossom, "almost_locked_set", "Death Blossom", 37, 360, True),
    "als_xy_wing": Strategy(almost_locked_set.als_xy_wing, "almost_locked_set", "ALS-XY-Wing", 38, 330, True),
    "hidden_triplet": Strategy(subsets.hidden_triplet, "subsets", "Hidden Triplet", 39, 100, True),
    "squirmbag": Strategy(fish.squirmbag, "fish", "Squirmbag", 40, 470, True),
    "naked_quad": Strategy(subsets.naked_quad, "subsets", "Naked Quad", 41, 120, True),
    "hidden_quad": Strategy(subsets.hidden_quad, "subsets", "Hidden Quad", 42, 150, True),
    "almost_locked_candidates": Strategy(questionable.almost_locked_candidates, "questionable",
                                         "Almost Locked Candidates", 43, 320, True),
    "franken_x_wing": Strategy(questionable.franken_x_wing, "questionable", "Franken X-Wing", 44, 300, True),
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
        for _, strategy in solver_strategies.items():
            if strategy.active:
                kwargs = strategy.solver(solver_status, board, window)
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
