# -*- coding: UTF-8 -*-

""" SOLVER CONFIGURATOR """

import sys
import os
from pathlib import Path
import argparse

from utils import set_puzzle_imput_file, check_file


def _set_config_defaults(args, config, data):
    """ set default values of config parameters """
    config["fname"] = None
    config["image"] = None
    config["snapshot"] = args.picture
    config["puzzles"] = args.input
    config["webcam"] = args.webcam
    config["cnn_model"] = args.model
    config["debug"] = args.debug
    config["chance"] = args.chance
    config["guess"] = args.guess
    config["repeat"] = args.repeat
    config["verbose"] = args.verbose
    config["first_id"] = args.first
    config["last_id"] = args.last
    if args.sel is not None:
        config["first_id"] = args.sel
        config["last_id"] = args.sel
    config["techniques"] = args.techniques
    config["method_stats"] = args.stats
    config["graphical_mode"] = args.txt
    config["peep"] = args.peep
    config["log_fname"] = args.log
    config["write_to_log"] = bool(config["log_fname"])
    config["log_csv_format"] = False
    config["puzzles_list"] = False
    config["is_solved"] = False
    config["output_opts"] = None
    config["stats"] = False
    config["ocr"] = False   # checking integrity of OCR scan - no solver output

    set_puzzle_imput_file(args.sudoku, config, data)
    data["error_data"] = config["cnn_model"]        # TODO
    check_file(config["cnn_model"], data, additional_info="CNN model")

    return True


def _set_data_defaults(data):
    """ set default values of data values """
    data["current_sudoku"] = 1  # counter of sudoku puzzle
    data["current_loop"] = 0  # sudoku solver loop counter
    data["current_path"] = []  # solver current run path
    data["iter_counter"] = 0  # solver iterations counter
    data["min_iters"] = sys.maxsize  # minimum number of iterations found by solver
    data["shortest_paths"] = []  # list of shortest solver found paths
    data["all_paths"] = {}  # all solver runs paths database
    data["iterations"] = []  # iterations per loop stats
    data["res_times"] = []  # resolution time per loop stats
    data["failures"] = 0  # total number of failures
    data["trials"] = []  # unsuccessful/successful trials to set a cell
    data["stat_iterations"] = []  # values of the number of iterations
    data["stat_runs"] = []  # runs per iteration statistic
    data["stat_unique_paths"] = []  # number of unique paths per iteration statistic
    data["graph_display"] = None

    # TODO
    data["stat_opts"] = []  # options statistics TO-DO
    data["tot_iterations"] = 0
    data["tot_solution_time"] = 0.0
    data["iterated"] = 0
    data["max_iterations"] = 0

    data["error_data"] = ""


def _output_single(config):
    output_opts = {
        "board_start": True,
        "board_iteration": False,
        "board_solved": True,
        "results": True,
        "iterations": False,
        "header_line": True,
        "plot_paths_stats": False,
    }
    if config["verbose"] == 0:
        output_opts["board_start"] = False
        output_opts["board_solved"] = False
        output_opts["results"] = False
    elif config["verbose"] == 2:
        output_opts["iterations"] = True
    elif config["verbose"] == 3:
        output_opts["iterations"] = True
        output_opts["board_iteration"] = True
    elif config["verbose"] == 4:
        config["stats"] = True

    config["output_opts"] = output_opts


def _output_list(config):
    output_opts = {
        "board_start": False,
        "board_iteration": False,
        "board_solved": False,
        "results": True,
        "results_in_line": True,
        "iterations": False,
        "header_line": True,
        "plot_paths_stats": False,
    }
    if config["verbose"] == 0:
        output_opts["results"] = False
    elif config["verbose"] == 2:
        output_opts["board_start"] = True
        output_opts["board_solved"] = True
        output_opts["results_in_line"] = False
    elif config["verbose"] == 3:
        output_opts["board_start"] = True
        output_opts["board_solved"] = True
        output_opts["results_in_line"] = False
        output_opts["iterations"] = True
    elif config["verbose"] == 4:
        output_opts["board_start"] = True
        output_opts["board_solved"] = True
        output_opts["results_in_line"] = False
        config["stats"] = True
    config["output_opts"] = output_opts


def set_output_options(config):
    """ set configuration of output results display """
    if config["puzzles_list"]:
        _output_list(config)
    else:
        _output_single(config)


def set_solver_options(config, data):
    """ set solver data structure, parse command line options amd set solver configuration

    TODO:
        - ignore the following options when OCR'ing sudoku input video or picture file:
          --guess
          --repeat
          --first
          --last
    """

    _set_data_defaults(data)
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'sudoku',
        metavar='sudoku',
        type=str,
        default='',
        nargs='?',
        help='sudoku puzzle(s) definition file')
    parser.add_argument(
        # "-p",
        "--picture",
        help="use webcam to take sudoku board picture and use it as input file",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=os.path.join(os.path.abspath(os.getcwd()), 'puzzles'),  # /2021_01'),
        help="path to sudoku input files folder"
    )
    parser.add_argument(
        "-w",
        "--webcam",
        type=str,
        default=os.path.join(str(Path.home()), 'Pictures', 'Webcam'),
        help="path to webcam image folder",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="./cnn_models/neuralNetMLP.pkl",
        help="pathname of a trained neural network digit classifier"
    )
    parser.add_argument(
        "-c",
        "--chance",
        help="when iterating, randomly select next cell to solve",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-g",
        "--guess",
        help="always select the right entry out of available options if iterating",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-r",
        "--repeat",
        help="solve each puzzle REPEAT times (REPEAT ≥ 1)",
        type=int,
        default=1,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="select level of output details",
        type=int,
        choices=[0, 1, 2, 3, 4],
        default=1,
    )
    parser.add_argument(
        "-f",
        "--first",
        help="solve puzzles starting with FIRST sudoku (1 ≤ FIRST ≤ LAST)",
        type=int,
        default=1,
    )
    parser.add_argument(
        "-l",
        "--last",
        help="stop after solving LAST sudoku (LAST ≥ 1 or LAST ≥ FIRST)",
        type=int,
        default=None,
    )
    parser.add_argument(
        "-e",
        "--sel",
        help="solve SEL puzzle from the list (1 ≤ SEL ≤ list length)",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--log", type=str, help="alternative output log filename", default=None
    )
    parser.add_argument(
        "-t",
        "--techniques",
        type=str,
        help="basic techniques used for solving a sudoku",
        default="muphoyirjxst"      # "muhoyirpxstqj"  TODO
    )
    parser.add_argument(
        "-p",
        "--peep",
        type=str,
        help="have a look at working of the selected solving techniques",
        default=""  # "mgvnuhoyirjqxspt"
    )
    parser.add_argument(
        "-s",
        "--stats",
        action="store_true",
        default=False,
        help="whether to show sudoku solving methods statistics"
    )
    parser.add_argument(
        "-x",
        "--txt",
        action="store_false",
        default=True,
        help="run the application in text mode only"
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="whether to show steps of image ocr"
    )

    args = parser.parse_args()
    _set_data_defaults(data)
    _set_config_defaults(args, config, data)
