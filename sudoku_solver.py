# -*- coding: UTF-8 -*-

""" SUDOKU SOLVER

    GLOBAL FUNCTIONS:
        main() - main pipeline of solving sudoku puzzles: handles different ways of defining
                 the puzzle (text file, image or video ocr), also manages list of puzzles

    LOCAL FUNCTIONS:
        _picture_ocr() - uses image file to define the puzzle
        _video_ocr() - uses video to define the puzzle
        _solve_sudoku_puzzle() - solves a sudoku puzzle: handles running the solver multiple times
        _run_solver() - finds solution of the current sudoku puzzle
        _apply_standard_techniques() - solver wrapper for handling unexpected exceptions
        _try_standard_techniques() - solver wrapper for handling expected exceptions
        _apply_brute_force() - solves the sudoku by guessing clues of selected empty cells
        _next_cell_to_resolve() - selects next empty cell to be resolved by 'brute force' method
        _init_board() - initializes the current sudoku board before running the solver
        _reset_solver_runs_data() - resets a sudoku solver multiple runs data
        _read_boards() - reads the sudoku board(s) definition file
        _run_in_silence() - runs the application with minimum output information
        _update_shortest_path_data() - updates data corresponding to the shortest path
        _update_all_paths_data() - updates database of all solver paths data
        _get_methods() - returns list of (strategy.name, strategy.solver) tuples

TODO:
    - video_ocr() needs to properly handle failures of _run_solver()
    - to clean displaying multiple sudoku definition file (right now there is no information
      when displaying results in-line (verbose = 1) and redundant information when displaying
      detailed results (verbose > 1)
     -integrate the main data structures: data, config, boards, board, and solver_status, remove
      redundancies and simplify interfaces between solver modules/functions
"""

import copy
import sys
import os
import re
import random
import time
import math

from progress.bar import Bar

from solver import solver_loop, get_prioritized_strategies
from solver import solver_status, board_image_stack, iter_stack, solver_status_stack

from opts import set_solver_options, set_output_options
from graph_utils import quit_btn_clicked

import display
import graphics
import sudoku_ocr
from utils import eliminate_options, DeadEndException


config = {}
data = {}
boards = {}
board = []
methods = []


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


def _picture_ocr():
    """ uses image file to define the puzzle """
    ocr_engine = sudoku_ocr.SudokuOCR(img_fname=config["image"])
    boards[0] = ocr_engine.sudoku_ocr()
    ocr_engine.show_contour(10)
    _init_board()
    if config['graphical_mode']:
        data["graph_display"] = graphics.AppWindow(board, solver_status, config["peep"])
    _solve_sudoku_puzzle()


def _video_ocr():
    """ uses video to define the puzzle """
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
    data["graph_display"] = graphics.AppWindow(board, solver_status, config["peep"])
    _solve_sudoku_puzzle()


def _solve_sudoku_puzzle():
    """ solve current sudoku puzzle
     - repeat the process config["repeat"] times to gather statistics,
       as per solver configuration (this option is available only
       in textual mode)
     - output results according to command line options
    The return value (True or False) matters only in video_ocr() method
    i.e., when running the application in graphical mode
    """
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

    assert not config['graphical_mode']
    _reset_solver_runs_data()
    progress_bar = None
    if not config["puzzles_list"]:
        progress_bar = Bar("Run", max=config["repeat"])
        print("\r          ", end="")  # to mask the initial 'Run' title
    for data["current_loop"] in range(loop_start, config["repeat"]):
        data["current_path"].clear()
        data["iter_counter"] = 0
        if _run_solver(progress_bar):
            if data["critical_error"]:
                print(f'\n\n{display.screen_messages["critical_error"]}\n')
                sys.exit()
            if data["current_loop"] == -1:
                data["solved_board"] = board.copy()
            else:
                data["iterations"].append(data["iter_counter"])
                data["res_times"].append(data["resolution_time"])
                if config["stats"]:
                    _update_shortest_path_data()
                    _update_all_paths_data()
        elif data["current_loop"] != -1:
            data["failures"] += 1

    display.solver_statistics(config, data)
    return True


def _run_solver(progress_bar=None):
    """ Initialize the current sudoku board and resolve the puzzle.
    Return: True if the sudoku puzzle was solved, False otherwise
     - If critical error occurred when running the solver in
       textual mode then data["critical_error"] flag is set True
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

    # the code below is executed only when running the
    # solver in textual mode or when calculating the
    # reference board (option -g)
    if not data["critical_error"]:
        data["resolution_time"] = time.time() - start_time
        if data["current_loop"] == 0:
            data["tot_solution_time"] += data["resolution_time"]
            data["tot_iterations"] += data["iter_counter"]
            data["iterated"] += 1 if data["iter_counter"] > 0 else 0
            data["max_iterations"] = max(data["max_iterations"], data["iter_counter"])
        config["is_solved"] = ret_code
        display.sudoku_board(config, data, board)
    return ret_code


def _apply_standard_techniques():
    """ This version of calling solver_loop() is used when
    'critical error' type failure of solver methods is
    unexpected
     - then the exception causes rising data["critical_error"] flag but
     the return value is True to avoid calling brute force method
    """
    try:
        return solver_loop(board, data["graph_display"], data)
    except DeadEndException:
        data["critical_error"] = True
        return True


def _try_standard_techniques():
    """ This version of calling solver_loop() is used when
    failure of the function is expected i.e. when checking
    which candidate makes clue) within  apply_brute_force() method
     - than the exception  is 'translated' into False return value
    """
    try:
        solver_loop(board, data["graph_display"], data)
        return True
    except DeadEndException:
        return False


def _apply_brute_force():
    """ try to resolve the sudoku puzzle by guessing an empty cell clue and then
    calling stack of standard techniques
    The sequence is repeated recursively until the puzzle is solved
    (or critical error occurs - then DeadEndException is being raised)
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

        to_eliminate = {(option, next_cell) for option in board[next_cell] if option != value}
        solver_status.capture_baseline(board, window)
        if window:
            window.options_visible = window.options_visible.union({next_cell})
        eliminate_options(solver_status, board, to_eliminate, window)

        if config["output_opts"]["iterations"] and data["current_loop"] == config["repeat"] - 1:
            display.iteration(config, data, board, next_cell, value)
        if config["stats"]:
            data["current_path"].append((data["current_loop"], next_cell // 9 + 1,
                                         next_cell % 9 + 1, value, board[next_cell], ))
        if window:
            window.draw_board(board, solver_tool="iterate", eliminate=to_eliminate, c_chain={next_cell: {(value, 'lime')}})

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


def _init_board():
    """ Initialize the current sudoku puzzle board """
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


def _read_boards():
    """ read a file containing definition of one or more sudoku puzzles
    The procedure is very flexible with respect of puzzle definition format:
    it has to be a text file containing 81 (or multiply of 81) characters from {'.', 0-9} set.
    The characters can be separated by any other characters. The subsequent characters
    are used to define the puzzle(s) board(s) by rows.
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
    """ runs the application with minimum output information  """
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


def _update_shortest_path_data():
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


def _get_methods():
    return [(strategy.name, strategy.solver) for strategy in get_prioritized_strategies().values() if strategy.active]


if __name__ == "__main__":
    main()
