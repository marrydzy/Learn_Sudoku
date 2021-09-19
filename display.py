# -*- coding: UTF-8 -*-

""" OUTPUT RESULTS FUNCTIONS """

import os
from pathlib import Path
import collections
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

screen_messages = {
    None: "",
    "plain_board": " ",
    "manual_entry": " ",
    "conflict": "Conflicting value",
    "full_house": "'Full House' technique",
    "visual_elimination": "'Visual Elimination' technique",
    "naked_singles": "'Naked Single' technique",
    "hidden_singles": "'Hidden Single' technique",
    "hidden_pairs": "'Hidden Pair' technique",     # TODO - obsolete!
    "hidden_pair": "'Hidden Pair' technique",
    "hidden_triplet": "'Hidden Triplet' technique",
    "hidden_quad": "'Hidden Quad' technique",
    "naked_twins": "'Naked Pair' technique",        # TODO - obsolete!
    "naked_pair": "'Naked Pair' technique",
    "naked_triplet": "'Naked Triplet' technique",
    "naked_quad": "'Naked Quad' technique",
    "omissions": "'Locked Candidates' technique",   # TODO - obsolete!
    "locked_candidates_type_1": "'Locked Candidates - Type 1 (Pointing)' technique",
    "locked_candidates_type_2": "'Locked Candidates - Type 2 (Claiming)' technique",
    "swordfish": "'Swordfish' technique",
    "finned_swordfish": "'Finned Swordfish' technique",
    "jellyfish": "'Jellyfish' technique",
    "x_wings": "'X-Wing' technique",
    "squirmbag": "'Squirmbag' technique",
    "finned_x_wings": "'Finned X-Wing' technique",
    "finned_jellyfish": "'Finned Jellyfish' technique",
    "finned_squirmbag": "'Finned Squirmbag' technique",
    "finned_rccb_mutant_x_wing": "'Finned RCCB Mutant X-Wing' technique",
    "finned_rbcc_mutant_x_wing": "'Finned RBCC Mutant X-Wing' technique",
    "finned_cbrc_mutant_x_wing": "'Finned CBRC Mutant X-Wing' technique",
    "sashimi_x_wing": "'Sashimi X-Wing (Double Fin)' technique",
    "sashimi_swordfish": "'Sashimi Swordfish' technique",
    "sashimi_jellyfish": "'Sashimi Jellyfish' technique",
    "sashimi_squirmbag": "'Sashimi Suirmbag' technique",
    "franken_x_wing": "'Franken X-Wing' technique",
    "xy_wing": "'XY-wing' technique",
    "y_wings": "'XY-Wing' techinique",              # TODO - obsolete!
    "xyz_wing": "'XYZ-Wing' technique",
    "wxyz_wing_type_1": "'WXYZ-Wing (Type 1)' technique",
    "wxyz_wing_type_2": "'WXYZ-Wing (Type 2)' technique",
    "wxyz_wing_type_3": "'WXYZ-Wing (Type 3)' technique",
    "wxyz_wing_type_4": "'WXYZ-Wing (Type 4)' technique",
    "wxyz_wing_type_5": "'WXYZ-Wing (Type 5)' technique",
    "w_wing": "'W-Wing' technique",
    "remote_pairs": "'Remote Pairs' technique",
    "skyscraper": "'skyscraper' technique",
    "sue_de_coq": "'Sue de Coq' technique",
    "empty_rectangle": "'Epmpty Rectangle' technique",
    "color trap": "'Simple Colors - Color Trap' technique",
    "color wrap": "'Simple Colors - Color Wrap' techinque",
    "multi_colors": "'Multi-Colors' technique",
    "multi_colors-color_wrap": "'Multi-Colors - Color Wrap' technique",
    "multi_colors-color_wing": "'Multi-Colors - Color Wing' techinque",
    # "x_colors": "'X-Colors' technique",
    "x_colors_elimination": "'X-Colors - elimination' technique",
    "x_colors_contradiction": "'X-Colors - contradiction' technique",
    "3d_medusa": "'3D Medusa' technique",
    "naked_xy_chain": "'Naked XY Chain' technique",
    "hidden_xy_chain": "'Hidden XY Chain' techinque",
    "scrub_pencil_marks": "WTF",
    "unique_values": "WTF",
    "unique_rectangles": "WTF",
    "uniqueness_test_1": "'Uniqueness Test 1' technique",
    "uniqueness_test_2": "'Uniqueness Test 2' technique",
    "uniqueness_test_3": "'Uniqueness Test 3' technique",
    "uniqueness_test_4": "'Uniqueness Test 4' technique",
    "uniqueness_test_5": "'Uniqueness Test 5' technique",
    "uniqueness_test_6": "'Uniqueness Test 6' technique",
    "observe": "Dupa Jaś",
    "end_of_game": "Sudoku solved!",
    "conflicting_values": "The entered value conflicts with other cells",
    "incorrect_value": "The entered value is incorrect!",
    "critical_error": "Critical error occurred due to inconsistent board data",
    "iterate": "Iterating ...",
    "almost_locked_candidates": "'Almost Locked Candidates' technique",
    "als_xz": "'ALS-XZ' technique",
    "als_xy_wing": "'ALS-XY-Wing' technique",
    "als_xy": "'ALS-XY' technique",
    "death_blossom": "'Death Blossom' technique",
    "hint_on_technique": "Suggested method to apply: ",
}

ERROR_MESSAGES = {
    'pathname_is_empty': 'ERROR: Pathname to {} is empty\n',
    'webcam_empty': 'ERROR: No .jpg files found in the folder {}\n',
    'file_not_exists': 'ERROR: No such file or directory: {}\n',
    'did_you_mean': 'Did you mean:',
    'contour_not_found': "ERROR: Couldn't find contour of sudoku board - try once again! {}\n",
}


def _get_digit(prompt, value_opts="123456789"):
    """ utility function to input one of the digits in value_opts string """
    while True:
        digit = input(prompt)
        if digit in value_opts:
            return digit
        print("Incorrect input value!")


def input_next_cell(board):
    """ get next cell index and value """
    print("\nCell to set:")
    row = int(_get_digit("Row = ")) - 1
    col = int(_get_digit("Col = ")) - 1
    next_cell = 9 * row + col
    clue = _get_digit("Value = ", board[next_cell])
    return next_cell, clue


def strategy_name(tool_name):
    """ Translate internal method name into strategy name """
    # TODO - this implementation is only proof of concept: use regular expressions
    #  in final implementation of the function
    strategy = tool_name
    if strategy.find("_wing"):
        strategy = strategy.replace("_wing", "-Wing")
    return strategy.title()


def puzzle_filename(config, data):
    """ write sudoku puzzle filename if output of sudoku solver is directed
    to a log file, as applicable
    """
    if data["current_loop"] == 0 and config["write_to_log"] and not config["puzzles_list"]:
        output_lines = []
        if not config["log_csv_format"] and Path(config["log_fname"]).is_file():
            output_lines.append("\n\n")
        output_lines.append(
            f"Sudoku puzzle definition file: {os.path.abspath(config['fname']):<s}\n"
        )
        with open(config["log_fname"], "a") as logfile:
            for line in output_lines:
                logfile.write(line)


def puzzle_id(config, data):
    """ outputs current puzzle number """
    output_lines = []
    output_lines.append(f'\nPuzzle # {data["current_sudoku"]}\n')
    output_lines.append("─" * len(output_lines[0].strip()) + "\n")
    _output_results(config, output_lines)


def sudoku_board(config, data, board, in_iterations=False):
    """ Show the sudoku board - print it or write to the log file """
    displ_board = bool(
        config["output_opts"]["board_start"]
        and not config["is_solved"]
        and data["current_loop"] == 0
    )
    displ_fname = displ_board and not in_iterations and (config["fname"] or config["image"])
    if not displ_board:
        displ_board = bool(config["output_opts"]["board_iteration"] and in_iterations)
    if not displ_board:
        displ_board = bool(
            config["output_opts"]["board_solved"]
            and config["is_solved"]
            and data["current_loop"] == config["repeat"] - 1
        )

    if displ_board:
        output_lines = []
        if displ_fname:
            sudoku = config["fname"] if config["fname"] else config["image"]
            if not config["graphical_mode"]:
                output_lines.append(sudoku + ':\n')
            else:
                output_lines.append(sudoku)
        if config["graphical_mode"] and data["graph_display"]:
            pass
            # data["graph_display"].draw_board(board, solver_tool="end_of_game" if config["is_solved"] else "plain_board")
        else:
            max_opt_len = max((len(board[n]) for n in range(81)))
            frm_sqr = " {:>" + str(max_opt_len) + "}"
            frm_opt = ("│" + frm_sqr * 3 + " ") * 3 + "│\n"
            top_line = (
                "┌"
                + ("─" + "─" * 3 * (max_opt_len + 1) + "┬") * 2
                + ("─" + "─" * 3 * (max_opt_len + 1) + "┐\n")
            )
            line = (
                "├"
                + ("─" + "─" * 3 * (max_opt_len + 1) + "┼") * 2
                + ("─" + "─" * 3 * (max_opt_len + 1) + "┤\n")
            )
            btm_line = (
                "└"
                + ("─" + "─" * 3 * (max_opt_len + 1) + "┴") * 2
                + ("─" + "─" * 3 * (max_opt_len + 1) + "┘\n")
            )

            for i in range(9):
                if i == 0:
                    output_lines.append(top_line)
                elif i % 3 == 0:
                    output_lines.append(line)
                output_lines.append(frm_opt.format(*[board[n] for n in range(9 * i, 9 * i + 9)]))
            output_lines.append(btm_line)
        _output_results(config, output_lines)


def _output_results(config, output_lines):
    if not output_lines or config["ocr"]:
        return

    if config["output_opts"]["header_line"]:
        output_lines.insert(0, "\n")
    config["output_opts"]["header_line"] = True

    if config["write_to_log"]:
        with open(config["log_fname"], "a") as logfile:
            for line in output_lines:
                logfile.write(line)
    else:
        for line in output_lines:
            print(line, end="")


def results(config, data, solver_ret_code):
    """ Output results of single run of the solver"""

    if config["puzzles_list"]:
        _list_puzzles_one_run_results(config, data, solver_ret_code)
    else:
        _one_puzzle_one_run_results(config, data, solver_ret_code)


def _one_puzzle_one_run_results(config, data, solver_ret_code):
    if config["ocr"]:
        return
    output_lines = []
    if solver_ret_code:
        if config["output_opts"]["results"]:
            output_lines.append(
                "Resolution time (ms):%7.2f\n" % (1000.0 * data["resolution_time"])
            )
            output_lines.append(
                "Number of iterations:   %4d\n" % (data["iter_counter"])
            )
        else:
            output_lines.append("Done!\n")
    else:
        output_lines.append("Oops, failed to find a solution\n")
    _output_results(config, output_lines)


def _one_puzzle_n_runs_results(config, data, res_time, iters):
    if config["ocr"]:
        return
    output_lines = []
    if config["output_opts"]["results"]:
        output_lines.append("Number of solver runs:        %6d\n" % config["repeat"])
        output_lines.append("Number of failures:           %6d\n" % data["failures"])
        output_lines.append(
            f"Average resolution time (ms):{res_time[0]:>7.2f}\n"
        )
        output_lines.append(
            f"Minimum resolution time (ms):{res_time[1]:>7.2f}\n"
        )
        output_lines.append(
            f"Maximum resolution time (ms):{res_time[2]:>7.2f}\n"
        )
        if iters[1] != iters[2]:
            output_lines.append(
                f"Average number of iterations:   {iters[0]:>4.0f}\n"
            )
            output_lines.append(
                f"Minimum number of iterations:   {iters[1]:>4d}\n"
            )
            output_lines.append(
                f"Maximum number of iterations:   {iters[2]:>4d}\n"
            )
        else:
            output_lines.append(
                f"Number of iterations:           {iters[1]:>4.0f}\n"
            )
    elif data["failures"] == 0:
        output_lines.append("Done without failure!\n")
    else:
        output_lines.append("Done with some failures!\n")
    _output_results(config, output_lines)


def _list_puzzles_one_run_results(config, data, solver_ret_code):
    output_lines = []
    sudoku_number = data["current_sudoku"]
    solved = "Solved" if solver_ret_code else "Failed"
    res_time = 1000.0 * data["resolution_time"]
    iterations = data["iter_counter"]
    if config["write_to_log"] and sudoku_number == config["first_id"]:
        if not config["log_csv_format"] and Path(config["log_fname"]).is_file():
            output_lines.append("\n\n")
        output_lines.append(
            f"Sudoku puzzles definitions file: {os.path.abspath(config['fname']):<s}\n"
        )
    if config["log_csv_format"]:
        if sudoku_number == config["first_id"]:
            output_lines.append("Puzzle #; Status; Resolution time; Iterations\n")
        output_lines.append(
            f"{sudoku_number:d}; {solved:s}; {res_time:.2f}; {iterations:d}\n"
        )
    else:
        if config["output_opts"]["results"] and config["output_opts"]["results_in_line"]:
            if sudoku_number == config["first_id"]:
                output_lines.append("Puzzle #  Status  Resolution time  Iterations\n")
            output_lines.append(
                "{:^8d}  {:>6s}     {:>7.2f}        {:>5d}\n".format(
                    sudoku_number, solved, res_time, iterations
                )
            )
            if sudoku_number > config["first_id"]:
                config["output_opts"]["header_line"] = False
        if config["output_opts"]["results"] and not config["output_opts"]["results_in_line"]:
            if solver_ret_code:
                output_lines.append("Resolution time (ms):%7.2f\n" % (res_time))
                output_lines.append("Number of iterations:   %4d\n" % (iterations))
            else:
                output_lines.append("Oops, failed to find a solution\n")

    if not config["output_opts"]["results"]:
        config["output_opts"]["header_line"] = False
    _output_results(config, output_lines)


def _list_puzzles_n_runs_results(config, data, res_time, iters):
    output_lines = []
    if config["write_to_log"] and data["current_sudoku"] == config["first_id"]:
        if not config["log_csv_format"] and Path(config["log_fname"]).is_file():
            output_lines.append("\n\n")
        output_lines.append(
            "Sudoku puzzles definitions file: {:<s}\n".format(
                os.path.abspath(config["sudoku_list_fname"])
            )
        )
    if config["log_csv_format"]:
        if data["current_sudoku"] == config["first_id"]:
            output_lines.append(
                "{:s}; {:s}; {:s}; {:s}; {:s}; {:s}; {:s}; {:s}; {:s}\n".format(
                    "", "", "", "resolution time", "", "", "iterations", "", ""
                )
            )
            output_lines.append(
                "{:s}; {:s}; {:s}; {:s}; {:s}; {:s}; {:s}; {:s}; {:s}\n".format(
                    "Sudoku #",
                    "runs",
                    "failures",
                    "mean",
                    "min",
                    "max",
                    "mean",
                    "min",
                    "max",
                )
            )
        output_lines.append(
            "{:d}; {:d}; {:d}; {:.2f}; {:.2f}; {:.2f}; {:.0f}; {:d}; {:d}\n".format(
                data["current_sudoku"],
                config["repeat"],
                data["failures"],
                res_time[0],
                res_time[1],
                res_time[2],
                iters[0],
                iters[1],
                iters[2],
            )
        )
    else:
        if config["output_opts"]["results"] and config["output_opts"]["results_in_line"]:
            if data["current_sudoku"] == config["first_id"]:
                output_lines.append(
                    "                                      Resolution time           Iterations\n"
                )
                output_lines.append(
                    "                %+7s %+7s %+7s %+7s %+7s %+7s %+7s %+7s \n"
                    % ("runs", "failed", "mean", "min", "max", "mean", "min", "max")
                )
            output_lines.append(
                "Sudoku #%-7d %7d %7d %7.2f %7.2f %7.2f %7.0f %7d %7d \n"
                % (
                    data["current_sudoku"],
                    config["repeat"],
                    data["failures"],
                    res_time[0],
                    res_time[1],
                    res_time[2],
                    iters[0],
                    iters[1],
                    iters[2],
                )
            )
            if data["current_sudoku"] > config["first_id"]:
                config["output_opts"]["header_line"] = False
            _output_results(config, output_lines)
        if config["output_opts"]["results"] and not config["output_opts"]["results_in_line"]:
            output_lines.append(
                "Number of solver runs:        %6d\n" % config["repeat"]
            )
            output_lines.append(
                "Number of failures:           %6d\n" % data["failures"]
            )
            output_lines.append(
                f"Average resolution time (ms):{res_time[0]:>7.2f}\n"
            )
            output_lines.append(
                f"Minimum resolution time (ms):{res_time[1]:>7.2f}\n"
            )
            output_lines.append(
                f"Maximum resolution time (ms):{res_time[2]:>7.2f}\n"
            )
            if iters[1] != iters[2]:
                output_lines.append(
                    f"Average number of iterations:   {iters[0]:>4.0f}\n"
                )
                output_lines.append(
                    f"Minimum number of iterations:   {iters[1]:>4d}\n"
                )
                output_lines.append(
                    f"Maximum number of iterations:   {iters[2]:>4d}\n"
                )
            else:
                output_lines.append(
                    f"Number of iterations:           {iters[1]:>4.0f}\n"
                )
            _output_results(config, output_lines)


def _digit_to_str(digit):
    translator = {
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
    }
    if digit in translator:
        return translator[digit]
    return str(digit)


def _show_shortest_routes(data, multi_paths, output_lines):
    unique_routes = _shortest_routes(data)
    if multi_paths or len(unique_routes) > 1:
        output_lines.append(
            "\n\nShortest found path{:s} that solve{:s} this sudoku:\n".format(
                "s" if len(unique_routes) > 1 else "",
                "" if len(unique_routes) > 1 else "s",
            )
        )
    else:
        output_lines.append("\n\nPath that solves this sudoku:\n")
    output_lines.append("-" * (len(output_lines[-1]) - 3) + "\n")

    route_number = 0
    for route in unique_routes:
        route_number += 1
        if len(unique_routes) > 1:
            output_lines.append(f"\nPath #{route_number:d}:\n")
        else:
            output_lines.append("\n")
        for step in route:
            output_lines.append(
                "cell({:d},{:d}): value = {:s} out of {:s}\n".format(*step)
            )


def _show_paths_stats(config, data, output_lines):
    output_lines.append("\nIterations number statistic:\n")
    output_lines.append("-" * (len(output_lines[-1]) - 2) + "\n")
    run_stats = {}
    for steps in data["iterations"]:
        if steps in run_stats:
            run_stats[steps] += 1
        else:
            run_stats[steps] = 1
    if len(run_stats) == 1:
        return False

    if not (config["puzzles_list"] or config["write_to_log"]):
        config["output_opts"]["plot_paths_stats"] = True
    l_runs = sorted(list(run_stats.keys()))
    output_lines.append("\nIterations:   Runs:  Unique paths:\n")
    for steps in l_runs:
        output_lines.append(
            "{:^10d}    {:^5d}       {:<4d}\n".format(
                steps, run_stats[steps], _get_unique_routes(data, steps)
            )
        )
        if config["output_opts"]["plot_paths_stats"]:
            data["stat_iterations"].append(steps)
            data["stat_runs"].append(run_stats[steps])
            data["stat_unique_paths"].append(_get_unique_routes(data, steps))

    return True


def methods_statistics(config, data, solving_methods):
    """ Output statistics on use of sudoku solving methods """

    output_lines = []
    output_lines.append('Solution methods statistics:\n============================\n')
    output_lines.append(f'puzzles required iteration:   {data["iterated"]}\n')
    output_lines.append(f'maximum number of iterations: {data["max_iterations"]}\n')
    output_lines.append(f'total number of iterations:   {data["tot_iterations"]}\n')
    tot_solving_time = int(data["tot_solution_time"])
    hrs = tot_solving_time // 3600
    min_time = (tot_solving_time // 60) % 60
    sec = tot_solving_time % 60
    output_lines.append(f'Total solving time (h:m:s):   {hrs:0>2d}:{min_time:0>2d}:{sec:0>2d}\n')

    table = []
    print()     # TODO - temporary only!
    for solving_method in solving_methods:
        table.append([solving_method[0],
                      solving_method[1].calls,
                      solving_method[1].options_removed + solving_method[1].clues,
                      solving_method[1].options_removed,
                      solving_method[1].clues,
                      solving_method[1].time_in,
                      (solving_method[1].options_removed + solving_method[1].clues) / solving_method[1].calls
                      if solving_method[1].calls > 0 else 0.0,
                      (solving_method[1].options_removed + solving_method[1].clues) / solving_method[1].time_in
                      if solving_method[1].time_in > 0 else 0.0])
        # print(f'{table[-1][0]}, :, {table[-1][2]}, {table[-1][5]}, {table[-1][6]}, {table[-1][7]}')
    _output_results(config, output_lines)

    headers = ["method", "method\ncalls", "  total\nhits", "options\nremoved", "  clues\nfound", "   time spent\n(sec)",
               "effectiveness\n(hits/call)", "   efficiency\n(hits/s)"]
    print()
    print(tabulate(table, headers, tablefmt="simple", floatfmt=".5f"))


def solver_statistics(config, data):
    """ Output statistics of multiple solver runs """
    res_time_stat = []
    iter_stat = []

    res_time_stat.append(1000.0 * sum(data["res_times"]) / float(config["repeat"]))
    res_time_stat.append(1000.0 * min(data["res_times"]))
    res_time_stat.append(1000.0 * max(data["res_times"]))
    iter_stat.append(int(sum(data["iterations"]) / float(config["repeat"])))
    iter_stat.append(min(data["iterations"]))
    iter_stat.append(max(data["iterations"]))

    output_lines = []
    if config["puzzles_list"]:
        _list_puzzles_n_runs_results(config, data, res_time_stat, iter_stat)
    else:
        _one_puzzle_n_runs_results(config, data, res_time_stat, iter_stat)
    if config["stats"] and iter_stat[1] > 0:
        paths = _show_paths_stats(config, data, output_lines)
        _show_shortest_routes(data, paths, output_lines)
        _output_results(config, output_lines)


def iteration(config, data, board, next_cell, value):
    """ show options and selection of current iteration """
    output_lines = []
    if (config["repeat"] > 1 and data["iter_counter"] == 1
            and data["current_loop"] == config["repeat"] - 1):
        _output_results(
            config,
            [
                f"Solver iterations in run # {data['current_loop'] + 1}:\n",
            ],
        )
    if config["output_opts"]["board_iteration"]:
        sudoku_board(config, data, board, True)
        config["output_opts"]["header_line"] = False
    if data["iter_counter"] > 1:
        config["output_opts"]["header_line"] = False
    output_lines.append(
        "Iteration {:2d}:   row = {:d}, col = {:d}, trying = {:s} out of {:s}\n".format(
            data["iter_counter"],
            next_cell // 9 + 1,
            next_cell % 9 + 1,
            value,
            board[next_cell],
        )
    )
    _output_results(config, output_lines)


def total_execution_time(config, tot_time):
    """ display program total run time """
    output_lines = []
    sec = tot_time % 60
    min_time = (tot_time // 60) % 60
    hrs = tot_time // 3600
    output_lines.append(
        f"\nTotal execution time (h:m:s): {hrs:02d}:{min_time:02d}:{sec:02d}\n"
    )
    output_lines.append("\n")
    _output_results(config, output_lines)


def _shortest_routes(data):
    """ select and return set of unique routes of the shortest length """
    routes_dict = {}
    for item in data["shortest_paths"]:
        if item[0] not in routes_dict.keys():
            routes_dict[item[0]] = []
        routes_dict[item[0]].append((item[1:]))
    unique_routes = set()
    for key in routes_dict:
        unique_routes.add(tuple(routes_dict[key]))
    return unique_routes


def _get_unique_routes(data, route_len):
    """ return number of unique routes of length 'route_len' """
    routes_dict = {}
    for item in data["all_paths"][route_len]:
        if item[0] not in routes_dict.keys():
            routes_dict[item[0]] = []
        routes_dict[item[0]].append((item[1:]))
    unique_routes = set()
    for key in routes_dict:
        unique_routes.add(tuple(routes_dict[key]))
    return len(unique_routes)


def _set_x_axis(data, bar_width):
    max_iters = data["stat_iterations"][-1]
    step = max(max_iters // 8, 1)
    if max_iters % step:
        max_iters = (max_iters // step + 1) * step
    labels = np.asarray(range(0, max_iters + step, step))
    ticks = labels.copy() + bar_width / 2
    return max_iters, ticks, labels


def plot_paths_stats(config, data):
    """plot bar chart of the number of iterations frequency and
    related number of unique solution paths"""
    nb_iterations = np.asarray(data["stat_iterations"])
    iter_frequency = np.asarray(data["stat_runs"]) * 100.0 / config["repeat"]
    bar_width = 0.3
    max_iters, ticks, labels = _set_x_axis(data, bar_width)

    _, ax1 = plt.subplots()
    ax1.set_xlim(0.0, max_iters + 1)
    plt.xticks(ticks, labels)
    plt.xlabel("Iterations")
    bars_1 = ax1.bar(
        nb_iterations, iter_frequency, width=bar_width, color="tab:blue", align="center"
    )
    plt.ylabel("% of runs")
    ax2 = ax1.twinx()
    bars_2 = ax2.bar(
        nb_iterations + bar_width,
        data["stat_unique_paths"],
        width=bar_width,
        color="chocolate",
        align="center",
    )
    plt.ylabel("# of unique paths")
    plt.legend([bars_1, bars_2], ["% of runs", "# of unique solution paths"])
    plt.title("Solver statistics")
    plt.show()


def plot_sel_stats_1(data):
    """ plot statistics related to iteration cell/options selection effectiveness """
    nb_iterations = np.asarray(range(1, data["stat_iterations"][-1] + 1))
    zeros = [0.0 for _ in range(data["stat_iterations"][-1] + 1)]
    y_less = np.asarray(zeros)
    y_more = np.asarray(zeros)
    for item in data["stat_opts"]:
        if item["opts_freq"][0] <= item["opts_freq"][1]:
            y_less[item["iters"]] += 1.0
        else:
            y_more[item["iters"]] += 1.0
    y_less *= 100.0 / len(data["stat_opts"])
    y_more *= 100.0 / len(data["stat_opts"])

    bar_width = 0.3
    max_iters, ticks, labels = _set_x_axis(data, bar_width)

    _, ax = plt.subplots()
    ax.set_xlim(0.0, max_iters + 1)
    plt.xticks(ticks, labels)
    plt.xlabel("Iterations")
    bars_1 = ax.bar(
        nb_iterations, y_less[1:], width=bar_width, color="tab:blue", align="center"
    )
    bars_2 = ax.bar(
        nb_iterations + bar_width,
        y_more[1:],
        width=bar_width,
        color="chocolate",
        align="center",
    )
    plt.ylabel("% of runs")
    plt.legend(
        [bars_1, bars_2],
        ["first option ≤ second option", "first option > second option"],
    )
    plt.title("Solver statistics: Frequencies of options (total)")
    plt.show()


def plot_sel_stats_2(data):
    """ plot statistics related to iteration cell/options selection effectiveness """

    nb_iterations = np.asarray(range(1, data["stat_iterations"][-1] + 1))
    zeros = [0.0 for _ in range(data["stat_iterations"][-1] + 1)]
    max_diff = np.asarray(zeros)
    sel_diff = np.asarray(zeros)
    itr_cntr = collections.defaultdict(int)
    for item in data["stat_opts"]:
        itr_cntr[item["iters"]] += 1

    for item in data["stat_opts"]:
        # print(data['stat_runs'])
        # print(item['iters'])
        max_diff[item["iters"]] += item["opts_max_min_freq"] / itr_cntr[item["iters"]]
        sel_diff[item["iters"]] += item["opts_diff"] / itr_cntr[item["iters"]]
    # print(itr_cntr)

    bar_width = 0.3
    max_iters, ticks, labels = _set_x_axis(data, bar_width)

    _, ax = plt.subplots()
    ax.set_xlim(0.0, max_iters + 1)
    plt.xticks(ticks, labels)
    plt.xlabel("Iterations")
    bars_1 = ax.bar(
        nb_iterations, sel_diff[1:], width=bar_width, color="tab:blue", align="center"
    )
    bars_2 = ax.bar(
        nb_iterations + bar_width,
        max_diff[1:],
        width=bar_width,
        color="chocolate",
        align="center",
    )
    plt.ylabel("% of runs")
    plt.legend([bars_1, bars_2], ["sel_diff", "max_diff"])
    plt.title("Solver statistics: opts freq difference")
    plt.show()


def error_message(error_type, data, additional_info=""):
    """ Display error message and quit """
    print('\n' + ERROR_MESSAGES[error_type].format(data["error_data"]
                                                   if additional_info == "" else additional_info))


def did_you_mean_message(error_type, data):
    """ Check if the user meant file_nameas puzzle input file  """
    print(f'\n - {ERROR_MESSAGES[error_type]} {data["error_data"]}?   (Yes/no)', end=' ')
    key = input()
    print()
    return bool(key == '' or key.lower() == 'y')
