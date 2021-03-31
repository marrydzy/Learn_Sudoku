# -*- coding: UTF-8 -*-

""" SUDOKU SOLVER

TO-DO:
    - to clean displaying multiple sudoku definition file (right now there is no information
      when displaying results in-line (verbose = 1) and redundant information when displaying
      detailed results (verbose > 1)
"""

import sys
import os
import re
import random
import time
import math

from progress.bar import Bar

from solver_manual import manual_solver
import solver_methods
import display
import graphics
import graph_utils
import sudoku_ocr
import opts
import research
from utils import is_solved


RESEARCH = False
DEBUG = True

config = {}
data = {}

boards = {}
board = []
board_image_stack = []
iter_stack = []

methods = []
lone_singles = []


def apply_standard_techniques():
    """
    For each cell that have been marked as 'solved' (was added to lone_singles)
    eliminate its value from options (pencil marks) in cell's row, column, and block
    (see Lone Singles at: https://www.learn-sudoku.com/lone-singles.html)
     - Then apply other solving techniques until no new lone singles are identified
       or the puzzle is solved.
    """

    def _erase_pencil_marks():
        if window:
            graph_utils.display_info(window, "Naked Singles")
            window.set_current_board(board)

        while lone_singles:
            cell = lone_singles.pop(0)
            value = board[cell]
            to_remove = []
            for one_cell in solver_methods.ALL_NBRS[cell]:
                if value in board[one_cell]:
                    to_remove.append((value, one_cell))
                    board[one_cell] = board[one_cell].replace(value, "")
                    if len(board[one_cell]) == 1:
                        lone_singles.append(one_cell)
                    elif not board[one_cell]:
                        return False
            if window:
                window.draw_board(board, "scrub_pencil_marks",
                                  new_clue=cell, remove=to_remove, singles=lone_singles,
                                  house=solver_methods.ALL_NBRS[cell])
        return True

    window = data["graph_display"] if config['graphical_mode'] else None
    if is_solved(board, window):
        return True

    report_stats = bool(config["method_stats"] and data["current_loop"] == 0)
    board_changed = True

    while board_changed:
        if lone_singles:
            if not _erase_pencil_marks():
                return False
        if is_solved(board, window):
            return True

        for method in methods[1:]:      # TODO - manual solution
            ret = method(board, window, lone_singles, report_stats)
            if ret is False:
                return False
            elif ret is True:
                board_changed = True
                break
            else:
                board_changed = False

    return True


def next_cell_to_resolve():
    """Return index of the next_cell cell to be resolved and an iterator of possible clues.
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

    if RESEARCH:
        research.collect_stats(
            data,
            "init_run",
            board=board,
            next_cell=next_cell,
            clue_options=clue_options,
            neighbours=solver_methods.ALL_NBRS,
        )
    return next_cell, clue_options


def find_cells_values():
    """ resolve the sudoku puzzle by recursively finding values of empty cells """
    next_cell, clue_iterator = next_cell_to_resolve()
    if next_cell is None:
        return True

    def _recreate_board():
        for cell_id, value in enumerate(board_image_stack[-1]):
            board[cell_id] = value

    board_image_stack.append(board.copy())
    iter_stack.append(clue_iterator)

    for value in iter_stack[-1]:
        data["iter_counter"] += 1
        _recreate_board()
        if config["graphical_mode"] and data["graph_display"]:  # TODO - redundant?
            data["graph_display"].set_current_board(board)      # TODO
        lone_singles.clear()
        board[next_cell] = value
        lone_singles.append(next_cell)

        if config["output_opts"]["iterations"] and data["current_loop"] == config["repeat"] - 1:
            display.iteration(config, data, board, next_cell, value)
        if config["stats"]:
            data["current_path"].append((data["current_loop"], next_cell // 9 + 1,
                                         next_cell % 9 + 1, value, board[next_cell], ))

        if config["graphical_mode"]:
            graph_utils.display_info(data["graph_display"], "Iterate")
            data["graph_display"].draw_board(board, "iterate", iterate=next_cell)  # TODO - fix it!

        if apply_standard_techniques() and find_cells_values():
            iter_stack.pop()
            board_image_stack.pop()
            if RESEARCH:
                research.collect_stats(data, "run_end")
            return True

    iter_stack.pop()
    _recreate_board()
    board_image_stack.pop()
    return False


def init_cells_options():
    """ Compile initial set of 'lone_singles' and initialize options of all empty cells """
    for cell_id in range(81):
        if board[cell_id] != ".":
            lone_singles.append(cell_id)
    cells_to_resolve = set(range(81)).difference(lone_singles)
    for cell_id in cells_to_resolve:
        board[cell_id] = "123456789"
    if data["graph_display"]:
        data["graph_display"].set_current_board(board)


def init_board():
    """ Initialize the sudoku board by reading the puzzle definition from the file """
    board.clear()
    for cell_id in range(81):
        board.append(boards[data["current_sudoku"] - 1][cell_id])
    if config['graphical_mode']:
        data["graph_display"] = graphics.AppWindow(board, config["peep"])
        if config['fname']:
            graph_utils.display_info(data["graph_display"], os.path.abspath(config['fname']))
    board_image_stack.clear()
    iter_stack.clear()


def run_solver(progress_bar=None):
    """Initialize the current sudoku board and resolve the puzzle.
    Return: True if the sudoku puzzle was solved, False otherwise
    """
    start_time = time.time()        # TODO
    init_board()
    data["iter_counter"] = 0
    config["is_solved"] = False
    display.puzzle_filename(config, data)
    display.sudoku_board(config, data, board)
    if progress_bar:
        if data["current_loop"] == 0:
            print()
            progress_bar.next()
        if data["current_loop"] > 0:
            progress_bar.next()
        if data["current_loop"] == config["repeat"] - 1:
            progress_bar.finish()

    # TODO - adding manual solution
    if data["graph_display"]:
        data["graph_display"].solver_loop = data["current_loop"]
        if data["graph_display"].solved_board is None and "solved_board" in data:
            data["graph_display"].solved_board = data["solved_board"]

    ret_code = methods[0](board, data["graph_display"], None)

    if not ret_code:
        ret_code = apply_standard_techniques()
        if ret_code and not is_solved(board, data["graph_display"] if config['graphical_mode'] else None):
            ret_code = find_cells_values()
    data["resolution_time"] = time.time() - start_time

    if data["graph_display"]:   # TODO
        data["resolution_time"] -= data["graph_display"].time_in

    if data["current_loop"] == 0:
        data["tot_solution_time"] += data["resolution_time"]
        data["tot_iterations"] += data["iter_counter"]
        data["iterated"] += 1 if data["iter_counter"] > 0 else 0
        data["max_iterations"] = max(data["max_iterations"], data["iter_counter"])
    config["is_solved"] = ret_code

    if config['graphical_mode'] and data["graph_display"]:  # TODO - redundatn?
        msg = f'The Sudoku solved in {1000.0 * data["tot_solution_time"]:.2f} ms' if ret_code else \
            "Oops... Failed to find the Sudoku solution"
        graph_utils.display_info(data["graph_display"], msg)     # TODO
    display.sudoku_board(config, data, board)
    return ret_code


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


def _solve_sudoku_puzzle():
    """ solve a sudoku puzzle and output results according to command line options """
    loop_start = -1 if config["guess"] else 0
    if config["repeat"] == 1:
        for data["current_loop"] in range(loop_start, 1):
            ret = run_solver()
            data["graph_display"].solved_board = 666
            if data["current_loop"] == -1:
                data["solved_board"] = board.copy()
        display.results(config, data, ret)
        return ret

    data["iterations"].clear()
    data["res_times"].clear()
    data["min_iters"] = sys.maxsize
    data["failures"] = 0
    data["all_paths"].clear()
    data["shortest_paths"].clear()
    progress_bar = None
    if not config["puzzles_list"]:
        progress_bar = Bar("Run", max=config["repeat"])
        print("\r          ", end="")  # to mask the initial 'Run' title
    for data["current_loop"] in range(loop_start, config["repeat"]):
        data["current_path"].clear()
        data["iter_counter"] = 0
        if not run_solver(progress_bar):
            data["failures"] += 1
        if data["current_loop"] == -1:
            data["solved_board"] = board.copy()
        else:
            data["iterations"].append(data["iter_counter"])
            data["res_times"].append(data["resolution_time"])
            if config["stats"]:
                _update_shortes_path_data()
                _update_all_paths_data()
    display.solver_statistics(config, data)
    return True  # DEBUG


def _read_boards():

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
    opts.set_output_options(config)


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


def _set_tools():
    techniques = {
        "m": (manual_solver, "manual_solution"),
        "u": (solver_methods.unique_values, "unique_values"),
        "h": (solver_methods.hidden_pairs, "hidden_pairs"),
        "p": (solver_methods.naked_twins, "naked_twins"),
        "o": (solver_methods.omissions, "omissions"),
        "y": (solver_methods.y_wings, "y_wings"),
        "i": (solver_methods.hidden_triplets, "hidden_triplets"),
        "j": (solver_methods.hidden_quads, "hidden_quads"),
        "t": (solver_methods.naked_triplets, "naked_triplets"),
        "q": (solver_methods.naked_quads, "naked_quads"),
        "r": (solver_methods.unique_rectangles, "unique_rectangles"),
        "x": (solver_methods.x_wings, "x_wings"),
        "s": (solver_methods.swordfish, "swordfish"),
    }

    tool_names = []
    for method in config["techniques"]:
        methods.append(techniques[method][0])
        tool_names.append(techniques[method][1])

    return tool_names, methods


def _video_ocr():
    # TODO - add graphical mode
    ocr_engine = sudoku_ocr.SudokuOCR()
    config["ocr"] = True
    while True:
        boards[0] = ocr_engine.sudoku_ocr()
        init_board()
        if _solve_sudoku_puzzle():
            break
        ocr_engine.image = None
        
    ocr_engine.show_contour()
    ocr_engine.close()
    config["ocr"] = False
    init_board()
    data["graph_display"] = graphics.AppWindow(board, config["peep"])  # TODO
    _solve_sudoku_puzzle()


def _picture_ocr():
    ocr_engine = sudoku_ocr.SudokuOCR(img_fname=config["image"])
    boards[0] = ocr_engine.sudoku_ocr()
    ocr_engine.show_contour(1000)
    init_board()
    if config['graphical_mode']:
        data["graph_display"] = graphics.AppWindow(board, config["peep"])
        data["graph_display"].display_info(os.path.abspath(config['image']))
    _solve_sudoku_puzzle()


def main():
    """ main pipeline of solving sudoku puzzle:
        - parse command line arguments, set solver options and tools
        - read input board(s) or OCR sudoku pictures
        - run solver for each puzzle (as specified)
        - print summary results
    """

    start_time = time.time()
    opts.set_solver_options(config, data)
    solver_tools, functions = _set_tools()
    _read_boards()
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
                        display.puzzle_id(config, data)     # TO DO
                    _solve_sudoku_puzzle()
    elif config["image"]:
        _picture_ocr()
    else:
        _video_ocr()

    display.total_execution_time(config, int(math.ceil(time.time() - start_time)))
    if config["output_opts"]["plot_paths_stats"]:
        display.plot_paths_stats(config, data)
        if RESEARCH:
            display.plot_sel_stats_1(data)
            display.plot_sel_stats_2(data)

    if config["method_stats"]:
        display.methods_statistics(config, data, zip(solver_tools, functions))
    print()


if __name__ == "__main__":
    main()
