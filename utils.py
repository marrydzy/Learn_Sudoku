# -*- coding: UTF-8 -*-

""" Utilities related to input files """

import os
import sys
import time
import glob
import difflib

from collections import defaultdict
from itertools import combinations
from pathlib import Path

from display import error_message, did_you_mean_message


def box_cells(k):
    """ return tuple of cells in k-th square """
    cells = []
    row = (k // 3) * 3
    col = (k % 3) * 3
    for offset in range(3):
        for cell in range((row + offset) * 9 + col, (row + offset) * 9 + col + 3):
            cells.append(cell)
    return tuple(cells)


def neighbour_cells(cell):
    """ return tuple of all cells crossing with the given cell """
    cells = set(CELLS_IN_ROW[cell // 9]).union(
        set(CELLS_IN_COL[cell % 9]).union(
            set(CELLS_IN_BOX[(cell // 27) * 3 + (cell % 9) // 3])
        )
    )
    cells.discard(cell)
    return cells


CELLS_IN_ROW = tuple(tuple(n for n in range(i * 9, (i + 1) * 9)) for i in range(9))
CELLS_IN_COL = tuple(tuple(n for n in range(i, 81, 9)) for i in range(9))
CELLS_IN_BOX = tuple(box_cells(i) for i in range(9))

ALL_NBRS = tuple(neighbour_cells(i) for i in range(81))
SUDOKU_VALUES_LIST = list('123456789')
SUDOKU_VALUES_SET = set('123456789')

CELL_ROW = tuple(i // 9 for i in range(81))
CELL_COL = tuple(i % 9 for i in range(81))
CELL_BOX = tuple((i // 27) * 3 + (i % 9) // 3 for i in range(81))


class DeadEndException(Exception):      # TODO
    pass


def get_stats(func):
    """ Decorator for getting solver method statistics """
    def function_wrapper(board, window, lone_singles):
        function_wrapper.calls += 1
        start = time.time()
        ret = func(board, window, lone_singles)
        function_wrapper.time_in += time.time() - start
        return ret

    function_wrapper.calls = 0
    function_wrapper.clues = 0
    function_wrapper.options_removed = 0
    function_wrapper.time_in = 0
    function_wrapper.__name__ = func.__name__
    return function_wrapper


def is_solved(board, solver_status):
    """ check if the board is solved """
    for row in range(9):
        clues = set(''.join(board[cell] for cell in CELLS_IN_ROW[row] if is_digit(cell, board, solver_status)))
        if clues != SUDOKU_VALUES_SET:
            return False
    for col in range(9):
        clues = set(''.join(board[cell] for cell in CELLS_IN_COL[col] if is_digit(cell, board, solver_status)))
        if clues != SUDOKU_VALUES_SET:
            return False
    for box in range(9):
        clues = set(''.join(board[cell] for cell in CELLS_IN_BOX[box] if is_digit(cell, board, solver_status)))
        if clues != SUDOKU_VALUES_SET:
            return False
    return True


def is_digit(cell_id, board, solver_status):
    """ return True if cell_id has been solved (is a digit and is not in 'solver_status.naked_singles'),
     False otherwise
    """
    return not bool(board[cell_id] == "." or len(board[cell_id]) != 1 or cell_id in solver_status.naked_singles)


def is_single(board, house, value):
    """ check if the value is a lone single in the house """
    values = ''.join(board[cell] for cell in house)
    if values.count(value) == 1:
        for cell in house:
            if value in board[cell]:
                return cell
    return None


def get_subsets(board, n_size_subset, als=False):
    """ generator of dictionaries of n-size subsets:
     - naked subsets if als == False
     - als'es if als == True
     The format of the 'subset' dictionary is: {candidate: {cell_1, ...}, ...}
     """
    for cells in (CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_BOX):
        for house in cells:
            unsolved = {cell for cell in house if len(board[cell]) > 1}
            if len(unsolved) > n_size_subset + 1:
                for subset in combinations(unsolved, n_size_subset):
                    candidates = set("".join(board[cell_id] for cell_id in subset))
                    expected_length = n_size_subset if not als else n_size_subset + 1
                    if len(candidates) == expected_length:
                        subset_data = defaultdict(set)
                        for cell in subset:
                            for candidate in board[cell]:
                                subset_data[candidate].add(cell)
                        yield house, subset_data


def get_impacting_cells(digit, greyed_out, board):
    """ return set of (solved) cells that impose restraint on the greyed-out cells """
    impacting_cells = set()
    for cell_id in greyed_out:
        impacting_cells = impacting_cells.union({cell for cell in ALL_NBRS[cell_id] if board[cell] == digit})
    return impacting_cells


def get_impacted_cells(board, subset):
    """ return set of unsolved cells impacted by subset cells """
    impacted_cells = set(range(81))
    for cell in subset:
        impacted_cells = impacted_cells.intersection(ALL_NBRS[cell])
    return {cell for cell in impacted_cells if len(board[cell]) > 1}


def get_impacted_houses(cell, base_house=None, to_eliminate=None):
    """ return union of houses the cell belongs to (cell row, column and box)
     - 'base_house' if not None is always included in the union of the cell houses
     - if 'to_eliminate' is neither None nor an empty set only the houses that intersect with
       it are included in the union of the cell houses
    """
    houses = base_house if base_house is not None else set()
    if to_eliminate is None:
        houses = houses.union(CELLS_IN_ROW[CELL_ROW[cell]])
        houses = houses.union(CELLS_IN_COL[CELL_COL[cell]])
        houses = houses.union(CELLS_IN_BOX[CELL_BOX[cell]])
    else:
        if to_eliminate.intersection(CELLS_IN_ROW[CELL_ROW[cell]]):
            houses = houses.union(CELLS_IN_ROW[CELL_ROW[cell]])
        if to_eliminate.intersection(CELLS_IN_COL[CELL_COL[cell]]):
            houses = houses.union(CELLS_IN_COL[CELL_COL[cell]])
        if to_eliminate.intersection(CELLS_IN_BOX[CELL_BOX[cell]]):
            houses = houses.union(CELLS_IN_BOX[CELL_BOX[cell]])
    return houses


def get_bi_value_cells(board):
    """ return dictionary of bi-value cells """
    # 'bi-values' data structure: {(opt_1, opt_2): {cell_1, cell_2, ...}}
    bi_values = defaultdict(set)
    for idx in range(81):
        if len(board[idx]) == 2:
            bi_values[(board[idx][0], board[idx][1])].add(idx)
    return bi_values


def get_pair_house(pair):
    """ Return house of the cells pair """
    cell_a, cell_b = pair
    if CELL_ROW[cell_a] == CELL_ROW[cell_b]:
        return CELLS_IN_ROW[CELL_ROW[cell_a]]
    if CELL_COL[cell_a] == CELL_COL[cell_b]:
        return CELLS_IN_COL[CELL_COL[cell_a]]
    return CELLS_IN_BOX[CELL_BOX[cell_a]]


def get_strong_links(board):
    """ return dictionary ({value: {(c1, c2), ...}} of strong links """

    def _house_strong_links(house):
        values = ''.join(board[cell] for cell in house if len(board) > 1)
        for value in set(values):
            if values.count(value) == 2:
                pair = tuple([cell for cell in house if value in board[cell]])
                strong_links[value].add(pair)

    strong_links = defaultdict(set)
    for idx in range(9):
        _house_strong_links(CELLS_IN_ROW[idx])
        _house_strong_links(CELLS_IN_COL[idx])
        _house_strong_links(CELLS_IN_BOX[idx])
    return strong_links


def get_cell_candidates(cell_id, board, solver_status):
    """ return set of cell candidates """
    return SUDOKU_VALUES_SET.difference(
        ''.join(board[cell] for cell in ALL_NBRS[cell_id] if is_digit(cell, board, solver_status)))


def get_pairs(board, by_row):
    # 'pairs' data structure:
    # {(col_1, col_2): {value: [row_1, ...]}} for 'by row' direction
    # {(row_1, row_2): {value: [col_1, ...]}} for 'by col' direction
    pairs_dict = {}
    for idx in range(9):
        cells = CELLS_IN_ROW[idx] if by_row else CELLS_IN_COL[idx]
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        options = "".join([board[cell] for cell in unsolved])
        for value in set(options):
            if options.count(value) == 2:
                pair = tuple(j for j in range(9) if value in board[cells[j]])
                pair_item = pairs_dict.pop(pair, defaultdict(list))
                pair_item[value].append(idx)
                pairs_dict[pair] = pair_item
    return pairs_dict


def get_2_upto_n_candidates(board, digit, n, by_row):
    """ return dictionary of rows/columns nodes where there are 2 - n nodes
    per line with the 'digit' candidate
     - if 'by_row' is True, the returned data structure is {row: {col1, ...}, ...}
     - if 'by_row' if False, the returned data structure is {column: {row1,...}, ...}
    """
    nodes = {}
    for x_id in range(9):
        cells = CELLS_IN_ROW[x_id] if by_row else CELLS_IN_COL[x_id]
        candidates = "".join(board[cell] for cell in cells)
        if 1 < candidates.count(digit) <= n:
            nodes[x_id] = {y_id for y_id in range(9) if digit in board[cells[y_id]]}
    return nodes


def get_house_pairs(house, board):
    """ return dictionary of pairs in the house (row, column, or box) """
    # pairs data structure:
    # {pair: [cell_1, cell_2]}
    pairs_dict = defaultdict(list)
    pairs = [board[cell] for cell in house if len(board[cell]) == 2]
    for pair in set(pairs):
        if pairs.count(pair) == 2:
            for cell in house:
                if board[cell] == pair:
                    pairs_dict[pair].append(cell)
    return pairs_dict


def eliminate_options(solver_status, board, to_eliminate, window):
    """ utility function: removes options as per 'to_eliminate' list """
    for option, cell in to_eliminate:
        board[cell] = board[cell].replace(option, "")
        if not board[cell]:
            if window and solver_status.iteration == 0:
                window.critical_error = (cell, )
            else:
                raise DeadEndException
        elif len(board[cell]) == 1:
            solver_status.naked_singles.add(cell)


def place_digit(cell_id, digit, board, solver_status, window):
    """ establish the given digit as cell value
    Returns:
     - set of eliminated candidates (set of (digit, cell) tuples)
     - set of cells with visible candidates impacted by the elimination
    """
    if window:
        solver_status.capture_baseline(board, window)
    board[cell_id] = digit
    solver_status.cells_solved.add(cell_id)
    solver_status.naked_singles.discard(cell_id)

    impacted_cells = {cell for cell in ALL_NBRS[cell_id] if digit in board[cell]}
    eliminate = {(digit, cell) for cell in impacted_cells}
    if window:
        impacted_cells = {cell for cell in impacted_cells
                          if cell in window.options_visible or window.show_all_pencil_marks}
    eliminate_options(solver_status, board, eliminate, window)
    return eliminate, impacted_cells


def set_cell_candidates(cell_id, board, solver_status):
    """ Set cell remaining candidates """
    board[cell_id] = ''.join(get_cell_candidates(cell_id, board, solver_status))
    if len(board[cell_id]) == 1:
        solver_status.naked_singles.add(cell_id)


def set_neighbours_candidates(cell_id, board, window, solver_status):
    """ Set candidates of the cell neighbours.
    For 'visible' pencilmarks:
        - remove all options that are not allowed
        - if the set is empty, set allowed options and remove the cell
          from the set with 'visible' options """
    for cell in ALL_NBRS[cell_id]:
        if not is_digit(cell, board, solver_status):
            if cell in window.options_visible:
                updated_opts = set(board[cell]) & get_cell_candidates(cell, board, solver_status)
                if updated_opts:
                    board[cell] = ''.join(updated_opts)
                else:
                    board[cell] = ''.join(get_cell_candidates(cell, board, solver_status))
                    window.options_visible.remove(cell)
            else:
                board[cell] = ''.join(get_cell_candidates(cell, board, solver_status))
            if len(board[cell]) > 1 and cell in solver_status.naked_singles:
                solver_status.naked_singles.remove(cell)
            if len(board[cell]) == 1:
                solver_status.naked_singles.add(cell)


def set_remaining_candidates(board, solver_status):
    """ initialize remaining candidates for all unsolved cells """
    if not solver_status.pencilmarks:
        for cell in range(81):
            if not is_digit(cell, board, solver_status):
                nbr_clues = [board[nbr_cell] for nbr_cell in ALL_NBRS[cell]
                             if is_digit(nbr_cell, board, solver_status)]
                board[cell] = "".join(value for value in SUDOKU_VALUES_LIST if value not in nbr_clues)
                if len(board[cell]) == 1:
                    solver_status.naked_singles.add(cell)
        solver_status.pencilmarks = True


def check_file(pathname, data, additional_info=""):
    """ Check if the required files exist
    - otherwise show appropriate message and with error code = -1
    """
    if not pathname:
        error_message('pathname_is_empty', data, additional_info=additional_info)
        sys.exit(-1)

    if not os.path.isfile(pathname):
        error_message('file_not_exists', data)
        sys.exit(-1)


def set_puzzle_input_file(puzzle, config, data):
    """ Resolving sudoku puzzle definition filename
    Glossary:
    fname, filename, file_name - file name with or without extension
    pathname, path_name - absolute or relative path and file name
    path, dir - absolute or relative path to a folder

    If 'puzzle' is an empty string and config['snapshot'] is set True
    the procedure checks files in 'webcam' folder
    (the default one or user set) and returns pathname to the most
    recent file - if there are any files, otherwise it prints error message
    and quits the app

    If 'puzzle' is a file name only (with or without extension) then
    'puzzle' is augmented with a path to puzzles folder
    (the default one or user set)

    Then the procedure checks if 'puzzle' is a valid pathname to a file:
     - if Yes then and the file has .txt - type extension
    (the procedure check for ext.lower() == '.txt') then config["fname"]
    is set to 'puzzle', otherwise the 'puzzle' string is assigned to config["image"]
    (the procedure doesn't check if the file is a correct sudoku puzzle input)

    Otherwise, the procedure looks for existing files and matches
    the one with the closest name  ('Did you mean ... ?') by:
    - it compiles a list of files with .txt and .jpg - like extension
    - if 'puzzle' is equal to any fnmme.lower() in the list then
      'puzzle' is set to the fname
    - otherwise the procedure looks for 'close matches' - if the list
      is not empty and there is only one 'closest match' - it is proposed
      as the 'puzzle' ('Did you mean ... ? message)
    """

    def _assign_puzzle_input_file(fname):
        _, ext = os.path.splitext(fname)
        if ext.lower() == '.txt':
            config["fname"] = fname
        else:
            config["image"] = fname

    def _assign_webcam_input_file():
        image_fnames = os.path.join(config["webcam"], '*.jpg')
        images = glob.glob(image_fnames)
        if images:
            images = sorted(images, key=os.path.getmtime, reverse=True)
            _assign_puzzle_input_file(images[0])
            return True
        data["error_data"] = os.path.join(str(Path.home()), 'Pictures', 'Webcam')
        error_message("webcam_empty", data)
        sys.exit(-1)

    if puzzle:
        path, _ = os.path.split(puzzle)
        if not path:
            puzzle = os.path.join(config["puzzles"], puzzle)
        if os.path.isfile(puzzle):
            _assign_puzzle_input_file(puzzle)
            return True

        _, extension = os.path.splitext(puzzle)
        if not extension:
            existing_files = [puzzle+ext for ext in ('.txt', '.TXT', '.jpg', '.JPG')
                              if os.path.isfile(puzzle+ext)]
            if len(existing_files) == 1:
                puzzle = existing_files[0]
                _assign_puzzle_input_file(puzzle)
                return True

        path, _ = os.path.split(puzzle)
        likely_files = []
        for file_type in ('*.txt', '*.TXT', '*.jpg', '*.JPG'):
            likely_files.extend(glob.glob(os.path.join(path, file_type)))
        lower_case_alternatives = [filepath.lower() for filepath in likely_files]
        if puzzle.lower() in lower_case_alternatives:
            puzzle = likely_files[lower_case_alternatives.index(puzzle.lower())]
            _assign_puzzle_input_file(puzzle)
            return True

        likely_files = difflib.get_close_matches(puzzle, likely_files.copy(), cutoff=0.6)
        if likely_files:
            if len(likely_files) == 1 or (
                    difflib.SequenceMatcher(None, puzzle, likely_files[0]).ratio() >
                    difflib.SequenceMatcher(None, puzzle, likely_files[1]).ratio()):
                puzzle = likely_files[0]
                data["error_data"] = puzzle
                if did_you_mean_message('did_you_mean', data):
                    _assign_puzzle_input_file(puzzle)
                    return True

        data["error_data"] = puzzle
        error_message('file_not_exists', data)
        sys.exit(-1)
    elif config["snapshot"]:
        _assign_webcam_input_file()
    else:
        return True
