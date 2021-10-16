# -*- coding: UTF-8 -*-

""" SUDOKU SOLVER MANAGER
    CLASS DEFINITIONS:
        Strategy - named tuple
        Priority - named tuple
        ValueEntered - named tuple
        SolverStatus - class to store data needed to recover status of the puzzle solver
                       prior to a move

    GLOBAL FUNCTIONS:
        solver_manager() - manages the process (manual or automatic moves) of solving a given sudoku puzzle
        get_prioritized_strategies() - returns prioritized list of solver strategies (methods)
        get_strategy_name() - if strategy is in _solver_strategies then it returns the method name string
                              otherwise it returns screen_messages[strategy]

    LOCAL FUNCTIONS:
        _manual_move() - depending on board state: sets or removes entered digit as cell clue or candidate
        _the_same_as_value_set() - entered key is the same as clicked cell current value
        _other_than_value_set() - entered key is other than clicked cell current value
        _as_value_and_unresolved() - entered key as value of unresolved cell
        _as_candidate_and_unresolved() - entered key as candidate of unresolved cell
        _check_board_integrity() - check integrity of the current board (givens and cells values:
                                   candidates are ignored)

TODO:

"""

from sys import exit
from pygame import K_b, K_h, quit
from collections import defaultdict, namedtuple, OrderedDict

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_BOX
from utils import is_digit, is_solved, set_cell_candidates, set_neighbours_candidates, get_cell_candidates
from display import screen_messages

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

Strategy = namedtuple("Strategy", ["solver", "technique", "name", "difficulty_rate", "active"])
Priority = namedtuple("Priority", ["by_ranking", "by_hits", "by_effectiveness", "by_efficiency"])
ValueEntered = namedtuple("ValueEntered", ["cell", "value", "as_clue"])

_solver_strategies = {
    "full_house": Strategy(singles.full_house, "singles", "Full House", 4, True),
    "visual_elimination": Strategy(singles.visual_elimination, "singles", "Visual Elimination", 4, True),
    "naked_single": Strategy(singles.naked_single, "singles", "Naked Single", 4, True),
    "hidden_single": Strategy(singles.hidden_single, "singles", "Hidden Single", 14, True),
    "locked_candidates": Strategy(intersections.locked_candidates, "intersections", "Locked Candidates", 50, True),
    "locked_candidates_type_1": Strategy(None, "", "Locked Candidates - Type 1 (Pointing)", 0, False),
    "locked_candidates_type_2": Strategy(None, "", "Locked Candidates - Type 2 (Claiming)", 0, False),
    "naked_pair": Strategy(subsets.naked_pair, "subsets", "Naked Pair", 60, True),
    "hidden_pair": Strategy(subsets.hidden_pair, "subsets", "Hidden Pair", 70, True),
    "three_d_medusa": Strategy(coloring.three_d_medusa, "coloring", "3D Medusa", 320, True),
    "finned_x_wing": Strategy(fish.finned_x_wing, "fish", "Finned X-Wing", 130, True),
    "sashimi_x_wing": Strategy(fish.sashimi_x_wing, "fish", "Sashimi X-Wing", 130, True),  # TODO - testing only!
    "x_wing": Strategy(fish.x_wing, "fish", "X-Wing", 100, True),
    "xy_wing": Strategy(wings.xy_wing, "wings", "XY-Wing", 160, True),
    "xyz_wing": Strategy(wings.xyz_wing, "wings", "XYZ-Wing", 180, True),
    # "three_d_medusa": Strategy(coloring.three_d_medusa, "coloring", "3D Medusa", 320, True),
    "swordfish": Strategy(fish.swordfish, "fish", "Swordfish", 140, True),
    # "xy_wing": Strategy(wings.xy_wing, "wings", "XY-Wing", 160, True),
    # "xyz_wing": Strategy(wings.xyz_wing, "wings", "XYZ-Wing", 180, True),
    "wxyz_wing": Strategy(wings.wxyz_wing, "wings", "WXYZ-Wing", 240, True),
    "wxyz_wing_type_1": Strategy(None, "", "WXYZ-Wing (Type 1)", 0, False),
    "wxyz_wing_type_2": Strategy(None, "", "WXYZ-Wing (Type 2)", 0, False),
    "wxyz_wing_type_3": Strategy(None, "", "WXYZ-Wing (Type 3)", 0, False),
    "wxyz_wing_type_4": Strategy(None, "", "WXYZ-Wing (Type 4)", 0, False),
    "wxyz_wing_type_5": Strategy(None, "", "WXYZ-Wing (Type 5)", 0, False),
    "w_wing": Strategy(wings.w_wing, "wings", "W-Wing", 150, True),
    "naked_triplet": Strategy(subsets.naked_triplet, "subsets", "Naked Triplet", 80, True),
    "test_1": Strategy(uniqueness_tests.test_1, "uniqueness_tests", "Uniqueness Test 1", 100, True),
    "test_2": Strategy(uniqueness_tests.test_2, "uniqueness_tests", "Uniqueness Test 2", 100, True),
    "test_3": Strategy(uniqueness_tests.test_3, "uniqueness_tests", "Uniqueness Test 3", 100, True),
    "test_4": Strategy(uniqueness_tests.test_4, "uniqueness_tests", "Uniqueness Test 4", 100, True),
    "test_5": Strategy(uniqueness_tests.test_5, "uniqueness_tests", "Uniqueness Test 5", 100, True),
    "test_6": Strategy(uniqueness_tests.test_6, "uniqueness_tests", "Uniqueness Test 6", 100, True),
    # "skyscraper": Strategy(intermediate_techniques.skyscraper, "Single Digit Patterns", "Skyscraper", 130, True),
    # "x_wing": Strategy(fish.x_wing, "fish", "X-Wing", 100, True),
    "jellyfish": Strategy(fish.jellyfish, "fish", "Jellyfish", 470, True),
    # "finned_x_wing": Strategy(fish.finned_x_wing, "fish", "Finned X-Wing", 130, True),
    # "sashimi_x_wing": Strategy(fish.sashimi_x_wing, "fish", "Sashimi X-Wing", 130, True),    # TODO - testing only!
    "finned_swordfish": Strategy(fish.finned_swordfish, "fish", "Finned Swordfish", 200, True),
    "sashimi_swordfish": Strategy(fish.sashimi_swordfish, "fish", "Sashimi Swordfish", 200, True),
    "finned_jellyfish": Strategy(fish.finned_jellyfish, "fish", "Finned Jellyfish", 240, True),
    "sashimi_jellyfish": Strategy(fish.sashimi_jellyfish, "fish", "Sashimi Jellyfish", 240, True),
    "finned_squirmbag": Strategy(fish.finned_squirmbag, "fish", "Finned Squirmbag", 470, True),
    "sashimi_squirmbag": Strategy(fish.sashimi_squirmbag, "fish", "Sashimi Squirmbag", 470, True),
    "finned_mutant_x_wing": Strategy(wings.finned_mutant_x_wing, "wings", "Finned Mutant X-Wing", 470, True),
    "finned_rccb_mutant_x_wing": Strategy(None, "", "Finned RCCB Mutant X-Wing", 0, False),
    "finned_rbcc_mutant_x_wing": Strategy(None, "", "Finned RBCC Mutant X-Wing", 0, False),
    "finned_cbrc_mutant_x_wing": Strategy(None, "", "Finned CBRC Mutant X-Wing", 0, False),
    "simple_colors": Strategy(coloring.simple_colors, "coloring", "Simple Colors", 150, True),
    "color_trap": Strategy(None, "", "Simple Colors - Color Trap", 0, False),
    "color_wrap": Strategy(None, "", "Simple Colors - Color Wrap", 0, False),
    "multi_colors": Strategy(coloring.multi_colors, "coloring", "Multi-Colors", 200, True),
    "multi_colors-color_wrap": Strategy(None, "", "Multi-Colors - Color Wrap", 0, False),
    "multi_colors-color_wing": Strategy(None, "", "Multi-Colors - Color Wing", 0, False),
    "x_colors": Strategy(coloring.x_colors, "coloring", "X-Colors", 200, True),
    "x_colors_elimination": Strategy(None, "", "X-Colors - Elimination", 0, False),
    "x_colors_contradiction": Strategy(None, "", "X-Colors - Contradiction", 0, False),
    # "three_d_medusa": Strategy(coloring.three_d_medusa, "coloring", "3D Medusa", 320, True),
    "naked_xy_chain": Strategy(coloring.naked_xy_chain, "coloring", "Naked XY Chain", 310, True),
    "hidden_xy_chain": Strategy(coloring.hidden_xy_chain, "coloring", "Hidden XY Chain", 310, True),
    "empty_rectangle": Strategy(intermediate_techniques.empty_rectangle, "intermediate_techniques",
                                "Empty Rectangle", 130, True),
    "sue_de_coq": Strategy(intermediate_techniques.sue_de_coq, "intermediate_techniques", "Sue de Coq technique",
                           130, True),
    "als_xy": Strategy(almost_locked_set.als_xy, "almost_locked_set", "ALS-XY", 320, True),
    "als_xz": Strategy(almost_locked_set.als_xz, "almost_locked_set", "ALS-XZ", 300, True),
    "death_blossom": Strategy(almost_locked_set.death_blossom, "almost_locked_set", "Death Blossom", 360, True),
    "als_xy_wing": Strategy(almost_locked_set.als_xy_wing, "almost_locked_set", "ALS-XY-Wing", 330, True),
    "hidden_triplet": Strategy(subsets.hidden_triplet, "subsets", "Hidden Triplet", 100, True),
    "squirmbag": Strategy(fish.squirmbag, "fish", "Squirmbag", 470, True),
    "naked_quad": Strategy(subsets.naked_quad, "subsets", "Naked Quad", 120, True),
    "hidden_quad": Strategy(subsets.hidden_quad, "subsets", "Hidden Quad", 150, True),
    "almost_locked_candidates": Strategy(questionable.almost_locked_candidates, "questionable",
                                         "Almost Locked Candidates", 320, True),
    "franken_x_wing": Strategy(questionable.franken_x_wing, "questionable", "Franken X-Wing", 300, True),
}


class SolverStatus:
    """ class to store data needed to recover status of the puzzle solver prior to a move """
    def __init__(self):
        self.pencilmarks = False
        self.iteration = 0
        self.givens = set()
        self.cells_solved = set()
        self.naked_singles = set()
        self.board_baseline = list()
        self.naked_singles_baseline = set()
        self.cells_solved_baseline = set()
        self.visible_pencilmarks_baseline = set()

    def initialize(self, board):
        self.givens = set(cell_id for cell_id in range(81) if board[cell_id] != ".")
        self.reset(board)

    def capture_baseline(self, board, window):
        if window and window.show_solution_steps:
            self.board_baseline = board.copy()
            self.naked_singles_baseline = self.naked_singles.copy()
            self.cells_solved_baseline = self.cells_solved.copy()
            self.visible_pencilmarks_baseline = window.options_visible.copy()
            if not window.animate:
                window.buttons[K_b].set_status(True)

    def restore_baseline(self, board, window):
        for cell_id in range(81):
            board[cell_id] = self.board_baseline[cell_id]
        self.naked_singles = self.naked_singles_baseline.copy()
        self.cells_solved = self.cells_solved_baseline.copy()
        window.options_visible = self.visible_pencilmarks_baseline.copy()

    def restore(self, solver_status_baseline):
        self.pencilmarks = solver_status_baseline.pencilmarks
        self.givens = solver_status_baseline.givens.copy()
        self.cells_solved = solver_status_baseline.cells_solved.copy()
        self.naked_singles = solver_status_baseline.naked_singles.copy()
        self.board_baseline = solver_status_baseline.board_baseline.copy()
        self.naked_singles_baseline = solver_status_baseline.naked_singles_baseline.copy()
        self.cells_solved_baseline = solver_status_baseline.cells_solved_baseline.copy()
        self.visible_pencilmarks_baseline = solver_status_baseline.visible_pencilmarks_baseline.copy()

    def reset(self, board):
        self.pencilmarks = False
        self.cells_solved.clear()
        self.naked_singles.clear()
        self.naked_singles_baseline.clear()
        self.cells_solved_baseline.clear()
        self.visible_pencilmarks_baseline.clear()
        for cell_id in range(81):
            if cell_id not in self.givens:
                board[cell_id] = "."
        self.board_baseline = board.copy()


solver_status = SolverStatus()


def solver_loop(board, window, data):
    """ Sudoku solving loop:
     - in graphical mode: draws current board and waits until one of predefined
       user interaction events happens (it is handled by _manual_move() function)
     - if user triggers application of defined solver tools the solution strategies
       are called according to a prioritized list until the board is updated or critical error occurs
     - when any of solution strategies (solver tools) is called it returns:
        - None or empty set when the strategy was unsuccessful (hasn't modified the board)
        - kwargs dictionary of parameters describing how the board was changed (the 'move' description)
     - if all solver tools were applied but the sudoku hasn't been solved yet (and no critical error
       occurred) then solver function returns False; otherwise it returns True
    """

    strategies = get_prioritized_strategies()
    kwargs = {"solver_tool": "plain_board_file_info"}

    while True:
        if window:
            window.draw_board(board, **kwargs)
            kwargs = _manual_move(board, window)
            if kwargs:
                continue
            if not window.calculate_next_clue:
                continue
            elif window.show_solution_steps:
                window.calculate_next_clue = False

        if is_solved(board, solver_status):
            return True

        for _, strategy in strategies.items():
            if strategy.active:
                kwargs = strategy.solver(solver_status, board, window)
                if kwargs:
                    if window:
                        if window.suggest_technique:
                            solver_status.restore_baseline(board, window)
                        if not window.critical_error:
                            window.critical_error, _ = _check_board_integrity(board, window)
                    break
        else:
            return False
        if data["current_loop"] == -1 and window and window.critical_error:
            print(f'\n{screen_messages["critical_error"]}\n')
            quit()
            exit()

    # the program should never get here!
    assert False


def get_prioritized_strategies():
    """ returns prioritized list of solver strategies (methods)"""
    # priorities = "by_ranking"             # 13-09-2021: 289 00:17:07
    # priorities = "by_hits"                # 13-09-2021: 293 00:19:55
    # priorities = "by_effectiveness"       # 13-09-2021: 271 02:40:14
    # priorities = "by_efficiency"          # 13-09-2021: 289 00:21:16
    priorities = "default"                  # 24-09-2021: 288 00:14:59

    strategy_priorities = {
        "Full House": Priority(4, 28, 45, 45),
        "Visual Elimination": Priority(4, 27, 37, 37),
        "Naked Single": Priority(4, 1, 1, 1),
        "Hidden Single": Priority(14, 2, 7, 4),
        "Locked Candidates": Priority(50, 3, 4, 3),
        "Naked Pair": Priority(60, 5, 8, 7),
        "Hidden Pair": Priority(70, 6, 2, 2),
        "Swordfish": Priority(140, 24, 14, 13),
        "XY-Wing": Priority(160, 13, 10, 9),
        "XYZ-Wing": Priority(180, 29, 19, 11),
        "WXYZ-Wing": Priority(240, 16, 21, 26),
        "W-Wing": Priority(150, 10, 13, 10),
        "Naked Triplet": Priority(80, 31, 39, 39),
        "Uniqueness Test 1": Priority(100, 11, 15, 5),
        "Uniqueness Test 2": Priority(100, 32, 26, 18),
        "Uniqueness Test 3": Priority(100, 20, 23, 19),
        "Uniqueness Test 4": Priority(100, 12, 16, 8),
        "Uniqueness Test 5": Priority(100, 36, 31, 31),
        "Uniqueness Test 6": Priority(100, 17, 27, 15),
        "Skyscraper": Priority(130, 26, 40, 40),
        "X-Wing": Priority(100, 33, 30, 30),
        "Jellyfish": Priority(470, 35, 43, 43),
        "Finned X-Wing": Priority(130, 14, 24, 23),
        "Sashimi X-Wing": Priority(130, 14, 24, 23),        # TODO - Testing only!
        "Finned Swordfish": Priority(200, 23, 17, 20),
        "Sashimi Swordfish": Priority(200, 23, 17, 20),     # TODO - Testing only!
        "Finned Jellyfish": Priority(240, 18, 25, 24),
        "Sashimi Jellyfish": Priority(240, 18, 25, 24),     # TODO - Testing only!
        "Finned Squirmbag": Priority(470, 25, 28, 27),
        "Sashimi Squirmbag": Priority(470, 25, 28, 27),     # TODO - Testing only!
        "Finned Mutant X-Wing": Priority(470, 22, 18, 12),
        "Simple Colors": Priority(150, 30, 38, 38),
        "Multi-Colors": Priority(200, 34, 9, 16),
        "X-Colors": Priority(200, 8, 11, 21),
        "3D Medusa": Priority(320, 4, 3, 6),
        "Naked XY Chain": Priority(310, 21, 20, 17),
        "Hidden XY Chain": Priority(310, 37, 35, 35),
        "Empty Rectangle": Priority(130, 38, 29, 29),
        "Sue de Coq technique": Priority(130, 39, 36, 36),
        "ALS-XY": Priority(320, 15, 22, 28),
        "ALS-XZ": Priority(300, 7, 6, 22),
        "Death Blossom": Priority(360, 40, 42, 42),
        "ALS-XY-Wing": Priority(330, 9, 5, 25),
        "Hidden Triplet": Priority(100, 19, 12, 14),
        "Squirmbag": Priority(470, 41, 44, 44),
        "Naked Quad": Priority(120, 42, 33, 33),
        "Hidden Quad": Priority(150, 43, 32, 32),
        "Almost Locked Candidates": Priority(320, 44, 41, 41),
        "Franken X-Wing": Priority(300, 45, 34, 34),
    }

    if priorities == "by_ranking":
        return OrderedDict(sorted(_solver_strategies.items(),
                                  key=lambda key_value_pair: strategy_priorities[key_value_pair[1].name].by_ranking
                                  if key_value_pair[1].name in strategy_priorities else 99999))
    elif priorities == "by_hits":
        return OrderedDict(sorted(_solver_strategies.items(),
                                  key=lambda key_value_pair: strategy_priorities[key_value_pair[1].name].by_hits
                                  if key_value_pair[1].name in strategy_priorities else 99999))
    elif priorities == "by_effectiveness":
        return OrderedDict(sorted(_solver_strategies.items(),
                                  key=lambda key_value_pair: strategy_priorities[
                                      key_value_pair[1].name].by_effectiveness
                                  if key_value_pair[1].name in strategy_priorities else 99999))
    elif priorities == "by_efficiency":
        return OrderedDict(sorted(_solver_strategies.items(),
                                  key=lambda key_value_pair: strategy_priorities[key_value_pair[1].name].by_efficiency
                                  if key_value_pair[1].name in strategy_priorities else 99999))
    else:
        return _solver_strategies


def get_strategy_name(strategy):
    if strategy in _solver_strategies:
        message = "'" + _solver_strategies[strategy].name + "' technique"
    else:
        message = screen_messages[strategy]
    return message


def _manual_move(board, window):
    """ Depending on board state: sets or removes entered digit as cell clue or candidate
         - checks board integrity after the move
         - checks if the board has been solved by the move
     """
    kwargs = {}
    if window and window.value_entered.cell is not None:
        solver_status.capture_baseline(board, window)
        cell_id, value, as_value = window.value_entered
        if cell_id in solver_status.cells_solved:
            if board[cell_id] == value:
                _the_same_as_value_set(board, window, solver_status.pencilmarks)
            else:
                _other_than_value_set(board, window, solver_status.pencilmarks)
        else:
            if as_value:
                _as_value_and_unresolved(board, window, solver_status.pencilmarks)
            else:
                _as_candidate_and_unresolved(board, window)

        conflicted_cells, incorrect_values = _check_board_integrity(board, window)
        conflicted = {window.value_entered.cell, } if window.value_entered.cell in conflicted_cells else set()
        c_chain = {cell: () for cell in conflicted_cells if cell != window.value_entered.cell}
        window.value_entered = ValueEntered(None, None, None)
        kwargs = {"solver_tool": "manual_entry",
                  "incorrect_values": incorrect_values,
                  "conflicted_cells": conflicted,
                  "c_chain": c_chain,
                  }
        window.buttons[K_h].set_status(True)
    if is_solved(board, solver_status) and window.solver_loop != -1:
        kwargs["solver_tool"] = "end_of_game"
    return kwargs


def _the_same_as_value_set(board, window, pencilmarks):
    """ Entered key is the same as clicked cell value """
    cell_id, value, as_value = window.value_entered
    solver_status.cells_solved.remove(cell_id)
    if as_value:
        if pencilmarks:
            set_cell_candidates(cell_id, board, solver_status)
        else:
            board[cell_id] = "."
    else:
        window.options_visible.add(cell_id)
        solver_status.naked_singles.add(cell_id)
    if pencilmarks:
        set_neighbours_candidates(cell_id, board, window, solver_status)


def _other_than_value_set(board, window, pencilmarks):
    """ Entered key other than clicked cell value """
    cell_id, value, as_value = window.value_entered
    if cell_id in solver_status.naked_singles:
        solver_status.naked_singles.remove(cell_id)
    board[cell_id] = value
    if as_value:
        solver_status.cells_solved.add(cell_id)
    else:
        solver_status.cells_solved.remove(cell_id)
        solver_status.naked_singles.add(cell_id)
        window.options_visible.add(cell_id)
    if pencilmarks:
        set_neighbours_candidates(cell_id, board, window, solver_status)


def _as_value_and_unresolved(board, window, pencilmarks):
    """ Entering key as value of unresolved cell """
    cell_id, value, _ = window.value_entered
    if cell_id in window.options_visible:
        window.options_visible.remove(cell_id)
    if cell_id in solver_status.naked_singles:
        solver_status.naked_singles.remove(cell_id)
    board[cell_id] = value
    solver_status.cells_solved.add(cell_id)
    if pencilmarks:
        set_neighbours_candidates(cell_id, board, window, solver_status)


def _as_candidate_and_unresolved(board, window):
    """ Entering key as candidate of unresolved cell """
    cell_id, value, _ = window.value_entered
    if cell_id in window.options_visible or window.show_all_pencil_marks:
        solver_status.naked_singles.discard(cell_id)
        if value in board[cell_id]:
            board[cell_id] = board[cell_id].replace(value, "")
            if len(board[cell_id]) == 0:
                set_cell_candidates(cell_id, board, solver_status)
                window.options_visible.discard(cell_id)
            elif len(board[cell_id]) == 1:
                solver_status.naked_singles.add(cell_id)
        else:
            board[cell_id] += value
            window.options_visible.add(cell_id)
    else:
        board[cell_id] = value
        solver_status.naked_singles.add(cell_id)
        window.options_visible.add(cell_id)


def _check_board_integrity(board, window):
    """ Check integrity of the current board (defined values and clues found):
     - for each row, column and box check if two or more cells have the same value
     - if solved board is defined, check entered values (clues) if they are correct
    """

    def _check_house(cells):
        values_dict = defaultdict(list)
        for cell in cells:
            if is_digit(cell, board, solver_status):
                values_dict[board[cell]].append(cell)
        conflicted = set()
        for value, in_cells in values_dict.items():
            if len(in_cells) > 1:
                conflicted = conflicted.union(in_cells)
        return conflicted

    conflicted_cells = set()
    for i in range(9):
        conflicted_cells = conflicted_cells.union(_check_house(CELLS_IN_ROW[i])).union(_check_house(CELLS_IN_COL[i])).\
                              union(_check_house(CELLS_IN_BOX[i]))
    incorrect_values = {cell for cell in range(81) if cell in solver_status.cells_solved and
                        board[cell] != window.solved_board[cell]} if window and window.solved_board else set()
    return conflicted_cells, incorrect_values


def _check_candidates(board, window):
    """ Check if visible candidates have correct values """
    c_chain = defaultdict(set)
    for cell in window.options_visible:
        if len(board[cell]) > 1:
            candidates = get_cell_candidates(cell, board)
            if candidates != set(board[cell]):
                for value in candidates.symmetric_difference(set(board[cell])):
                    c_chain[cell].add((value, 'pink'))
    return c_chain
