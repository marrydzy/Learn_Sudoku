# -*- coding: UTF-8 -*-

""" SUDOKU SOLVER

    GLOBAL FUNCTIONS:
        main() - main pipeline of solving sudoku puzzles

    LOCAL FUNCTIONS:
        _reset_solver_runs_data() - reset a sudoku solver runs data
        _solve_sudoku_puzzle() - solves a sudoku puzzle and outputs results according to command line options


TODO:
    - video_ocr() needs to properly handle failures of _run_solver()
    - to clean displaying multiple sudoku definition file (right now there is no information
      when displaying results in-line (verbose = 1) and redundant information when displaying
      detailed results (verbose > 1)
"""

import copy
import sys
import os
import re
import random
import time
import math

from progress.bar import Bar

from solver_manual import manual_solver, get_prioritized_strategies
from solver_manual import solver_status, board_image_stack, iter_stack, solver_status_stack

from opts import set_solver_options, set_output_options
from graph_utils import quit_btn_clicked

import display
import graphics
import sudoku_ocr
from utils import remove_options, DeadEndException


config = {}
data = {}
boards = {}
board = []
methods = []


def _try_standard_techniques():
    """ This version of calling manual_solver() is used when
    failure of the function is expected i.e. when checking
    which candidate makes clue) within  apply_brute_force() method
     - than the exception  is 'translated' into False return value
    """
    try:
        manual_solver(board, data["graph_display"], data, False)
        return True
    except DeadEndException:
        return False


def _apply_standard_techniques():
    """ This version of calling manual_solver() is used when
    'critical error' type failure of manual solver methods is
    unexpected
     - then the exception causes rising data["critical_error"] flag but
     the return value is True to avoid calling brute force method
    """
    try:
        return manual_solver(board, data["graph_display"], data, True)
    except DeadEndException:
        data["critical_error"] = True
        if data["current_loop"] != -1:
            data["failures"] += 1
        return True


def _next_cell_to_resolve():
    """ Return index of the next_cell cell to be resolved and an iterator of possible clues.
    The next_cell cell is always selected from the set of cells with the lowest number of options,
    either randomly or based on statistics of already set values.
    """

    cells_to_resolve = [(cell, len(board[cell])) for cell in range(81) if len(board[cell]) > 1]
    if not cells_to_resolve:
        return None, None

    cells_to_resolve.sort(key=lambda x: x[1])
    if config["chance"]:
        short_list = [item[0] for item in cells_to_resolve if item[1] == cells_to_resolve[0][1]]
        random.shuffle(short_list)
        next_cell = short_list[0]
        cell_options = list(board[next_cell])
        random.shuffle(cell_options)
        clue_options = "".join(cell_options)
    else:
        next_cell = cells_to_resolve[0][0]
        clue_options = board[next_cell]
        if config["guess"] and data["current_loop"] > -1:
            clue_options = data["solved_board"][next_cell]
    return next_cell, clue_options


def _apply_brute_force():
    """ try to resolve the sudoku puzzle by guessing value of an empty cell and then
    calling stack of standard techniques
    The sequence is repeated recursively until the puzzle is solved
    """

    next_cell, clue_iterator = _next_cell_to_resolve()
    if next_cell is None:
        return True

    def _restore_board():
        for cell_id, value in enumerate(board_image_stack[-1]):
            board[cell_id] = value

    board_image_stack.append(board.copy())
    iter_stack.append(clue_iterator)
    solver_status_stack.append(copy.deepcopy(solver_status))
    window = data["graph_display"]
    for value in iter_stack[-1]:
        data["iter_counter"] += 1
        solver_status.iteration = data["iter_counter"]
        _restore_board()
        solver_status.restore(solver_status_stack[-1])

        to_remove = {(option, next_cell) for option in board[next_cell] if option != value}
        solver_status.capture_baseline(board, window)
        if window:
            window.options_visible = window.options_visible.union({next_cell})
        remove_options(solver_status, board, to_remove, window)

        if config["output_opts"]["iterations"] and data["current_loop"] == config["repeat"] - 1:
            display.iteration(config, data, board, next_cell, value)
        if config["stats"]:
            data["current_path"].append((data["current_loop"], next_cell // 9 + 1,
                                         next_cell % 9 + 1, value, board[next_cell], ))
        if window:
            window.draw_board(board, solver_tool="iterate", remove=to_remove, c_chain={next_cell: {(value, 'lime')}})

        if _try_standard_techniques() and _apply_brute_force():
            iter_stack.pop()
            board_image_stack.pop()
            solver_status_stack.pop()
            return True

    iter_stack.pop()
    _restore_board()
    board_image_stack.pop()
    solver_status_stack.pop()
    return False


def _init_board():
    """ Initialize the current sudoku puzle board """
    board_image_stack.clear()
    iter_stack.clear()
    board.clear()
    for cell in range(81):
        board.append(boards[data["current_sudoku"] - 1][cell])
    if config['graphical_mode']:
        data["graph_display"].options_visible.clear()
        data["graph_display"].critical_error = None
        if config['fname']:
            display.screen_messages["plain_board_file_info"] = os.path.abspath(config["fname"])


def _update_shortes_path_data():
    """ update data corresponding to the shortest path """
    if data["iter_counter"] < data["min_iters"]:
        data["min_iters"] = data["iter_counter"]
        data["shortest_paths"].clear()
        data["shortest_paths"] = data["current_path"].copy()
    elif data["iter_counter"] == data["min_iters"]:
        for item in data["current_path"]:
            data["shortest_paths"].append(item)


def _update_all_paths_data():
    """ update database of all solver paths data """
    if data["iter_counter"] in data["all_paths"]:
        for item in data["current_path"]:
            data["all_paths"][data["iter_counter"]].append(item)
    else:
        data["all_paths"][data["iter_counter"]] = data["current_path"].copy()


def _read_boards():
    """ TODO
    """
    if config["fname"]:
        board_id = 0
        with open(config["fname"]) as lines:
            boards[board_id] = []
            for line in lines:
                for item in re.findall(r"[.0-9]", line):
                    boards[board_id].append(item if item != "0" else ".")
                if len(boards[board_id]) == 81:
                    board_id += 1
                    boards[board_id] = []
        del boards[board_id]

        if not config["last_id"] or config["last_id"] > len(boards):
            config["last_id"] = len(boards)
        if config["first_id"] < 1:
            config["first_id"] = 1
        if not 0 < config["first_id"] <= config["last_id"]:
            print("\nNothing to solve! - Please check the solver options\n")
            sys.exit(0)
        if config["last_id"] - config["first_id"] > 0:
            config["puzzles_list"] = True
    set_output_options(config)


def _run_in_silence():
    puzzles = config["last_id"] - config["first_id"] + 1
    print()
    progress_bar = Bar("Processing puzzles list", max=puzzles)
    for data["current_sudoku"] in range(config["first_id"], config["last_id"] + 1):
        progress_bar.next()
        _solve_sudoku_puzzle()
    progress_bar.finish()
    if data["failures"] == 0:
        print("\nDone without failure!")
    else:
        print("\nDone with some failures!")


def _get_methods():
    return [(strategy.name, strategy.solver) for strategy in get_prioritized_strategies().values() if strategy.active]


def _video_ocr():
    # TODO - add graphical mode
    ocr_engine = sudoku_ocr.SudokuOCR()
    config["ocr"] = True
    while True:
        boards[0] = ocr_engine.sudoku_ocr()
        _init_board()
        if _solve_sudoku_puzzle():
            break
        ocr_engine.image = None
        
    ocr_engine.show_contour()
    ocr_engine.close()
    config["ocr"] = False
    _init_board()
    data["graph_display"] = graphics.AppWindow(board, solver_status, config["peep"])  # TODO
    _solve_sudoku_puzzle()      # TODO: is it needed?


def _picture_ocr():
    ocr_engine = sudoku_ocr.SudokuOCR(img_fname=config["image"])
    boards[0] = ocr_engine.sudoku_ocr()
    ocr_engine.show_contour(10)
    _init_board()
    if config['graphical_mode']:
        data["graph_display"] = graphics.AppWindow(board, solver_status, config["peep"]) # TODO
        # data["graph_display"].display_info(os.path.abspath(config['image']))
    _solve_sudoku_puzzle()


""" -----------------------------------------------------------------------------------------------"""


def main():
    """ main pipeline of solving sudoku puzzles:
        - parse command line arguments, set solver options and tools
        - read input board(s) or OCR sudoku picture
        - run solver for each puzzle (as specified)
        - print summary results
    """

    start_time = time.time()
    set_solver_options(config, data)    # set solver data & configuration parameters
    _read_boards()
    if config['graphical_mode']:
        data["graph_display"] = graphics.AppWindow(board, solver_status, config["peep"])

    if boards:
        if not config["puzzles_list"]:
            data["current_sudoku"] = config["first_id"]
            _solve_sudoku_puzzle()
        else:
            if config["verbose"] == 0:
                _run_in_silence()
            else:
                for data["current_sudoku"] in range(config["first_id"], config["last_id"] + 1):
                    if not config["output_opts"]["results_in_line"]:
                        display.puzzle_id(config, data)
                    _solve_sudoku_puzzle()
    elif config["image"]:
        _picture_ocr()
    else:
        _video_ocr()

    display.total_execution_time(config, int(math.ceil(time.time() - start_time)))
    if config["output_opts"]["plot_paths_stats"]:
        display.plot_paths_stats(config, data)
    if config["method_stats"]:
        display.methods_statistics(config, data, _get_methods())
    print()


def _solve_sudoku_puzzle():
    """ solves a sudoku puzzle and outputs results according to command line options """
    loop_start = -1 if config["guess"] else 0
    ret = False
    if config["repeat"] == 1:
        for data["current_loop"] in range(loop_start, 1):
            ret = _run_solver()
            if data["critical_error"]:
                print(f'\n{display.screen_messages["critical_error"]}\n')
                if config['graphical_mode']:
                    quit_btn_clicked(data["graph_display"])
                else:
                    sys.exit()
            elif data["current_loop"] == -1:
                data["solved_board"] = board.copy()
        display.results(config, data, ret)
        return ret

    _reset_solver_runs_data()
    progress_bar = None
    if not config["puzzles_list"]:
        progress_bar = Bar("Run", max=config["repeat"])
        print("\r          ", end="")  # to mask the initial 'Run' title
    for data["current_loop"] in range(loop_start, config["repeat"]):
        data["current_path"].clear()
        data["iter_counter"] = 0
        if _run_solver(progress_bar):
            if data["current_loop"] == -1:
                data["solved_board"] = board.copy()
            else:
                data["iterations"].append(data["iter_counter"])
                data["res_times"].append(data["resolution_time"])
                if config["stats"]:
                    _update_shortes_path_data()
                    _update_all_paths_data()
        elif data["current_loop"] != -1:
            data["failures"] += 1

    display.solver_statistics(config, data)
    return True  # DEBUG


def _run_solver(progress_bar=None):
    """Initialize the current sudoku board and resolve the puzzle.
    Return: True if the sudoku puzzle was solved, False otherwise
    """
    start_time = time.time()
    _init_board()
    solver_status.initialize(board)
    data["iter_counter"] = 0
    config["is_solved"] = False
    display.puzzle_filename(config, data)
    display.sudoku_board(config, data, board)
    if progress_bar:
        if data["current_loop"] >= 0:
            if data["current_loop"] == 0:
                print()
            progress_bar.next()
        if data["current_loop"] == config["repeat"] - 1:
            progress_bar.finish()

    window = data["graph_display"]
    if window:
        window.solver_loop = data["current_loop"]
        if window.solved_board is None and "solved_board" in data:
            window.solved_board = data["solved_board"]

    ret_code = _apply_standard_techniques()
    if not ret_code:
        ret_code = _apply_brute_force()

    # TODO: the code below is executed only in non-graphical mode!
    data["resolution_time"] = time.time() - start_time
    if window:
        data["resolution_time"] -= window.time_in

    if data["current_loop"] == 0:
        data["tot_solution_time"] += data["resolution_time"]
        data["tot_iterations"] += data["iter_counter"]
        data["iterated"] += 1 if data["iter_counter"] > 0 else 0
        data["max_iterations"] = max(data["max_iterations"], data["iter_counter"])
    config["is_solved"] = ret_code
    display.sudoku_board(config, data, board)
    return ret_code


def _reset_solver_runs_data():
    """ reset a sudoku solver runs data
     - used when solving the sudoku more than once to collect statistics
     """
    data["iterations"].clear()
    data["res_times"].clear()
    data["min_iters"] = sys.maxsize
    data["critical_error"] = False
    data["failures"] = 0
    data["all_paths"].clear()
    data["shortest_paths"].clear()


if __name__ == "__main__":
    main()
