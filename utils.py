# -*- coding: UTF-8 -*-

""" Utilities related to input files """

import os
import sys
import glob
import difflib
from pathlib import Path
from display import error_message, did_you_mean_message


def block_cells(k):
    """ return tuple of cells in k'th square """
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
            set(CELLS_IN_SQR[(cell // 27) * 3 + (cell % 9) // 3])
        )
    )
    cells.discard(cell)
    return cells


CELLS_IN_ROW = tuple(tuple(n for n in range(i * 9, (i + 1) * 9)) for i in range(9))
CELLS_IN_COL = tuple(tuple(n for n in range(i, 81, 9)) for i in range(9))
CELLS_IN_SQR = tuple(block_cells(i) for i in range(9))

ALL_NBRS = tuple(neighbour_cells(i) for i in range(81))
SUDOKU_VALUES_LIST = list('123456789')
SUDOKU_VALUES_SET = set('123456789')

CELL_ROW = tuple(i // 9 for i in range(81))
CELL_COL = tuple(i % 9 for i in range(81))
CELL_SQR = tuple((i // 27) * 3 + (i % 9) // 3 for i in range(81))


class DeadEndException(Exception):
    pass


def is_solved(board, window):
    """ check if the board is solved """
    for row in range(9):
        clues = set(''.join(board[cell] for cell in CELLS_IN_ROW[row] if is_clue(cell, board, window)))
        if clues != SUDOKU_VALUES_SET:
            return False
    for col in range(9):
        clues = set(''.join(board[cell] for cell in CELLS_IN_COL[col] if is_clue(cell, board, window)))
        if clues != SUDOKU_VALUES_SET:
            return False
    for box in range(9):
        clues = set(''.join(board[cell] for cell in CELLS_IN_SQR[box] if is_clue(cell, board, window)))
        if clues != SUDOKU_VALUES_SET:
            return False
    return True


def is_clue(cell_id, board, window):
    """ check if the cell has clue (is solved) """
    if board[cell_id] == "." or len(board[cell_id]) != 1:
        return False
    if window:
        if not (cell_id in window.clues_defined or cell_id in window.clues_found):
            return False
    return True


def is_single(board, house, value):
    """ check if the value is a lone single in the house """
    values = ''.join(board[cell] for cell in house)
    if values.count(value) == 1:
        for cell in house:
            if value in board[cell]:
                return cell
    return None


# def are_cells_set(board, cells):
#     """ check if all cells are set """
#     return all([True if is_clue(cell_id, board, window) else False for cell_id in cells])


def get_options(cell, board, window):
    """ returns set of options of the cell """
    if is_clue(cell, board, window):
        return set(board[cell])
    else:
        return SUDOKU_VALUES_SET.copy() - set(''.join([board[cell_id] for cell_id in ALL_NBRS[cell]]))


def in_options(board, cell_id, value):
    """ check if the value can make correct clue of the cell """
    options = SUDOKU_VALUES_SET.copy() - set(''.join([board[cell_id] for cell_id in ALL_NBRS[cell_id]]))
    return True if value in options else False


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


def set_puzzle_imput_file(puzzle, config, data):
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
        _, extension = os.path.splitext(fname)
        if extension.lower() == '.txt':
            config["fname"] = fname
        else:
            config["image"] = fname

    def _assign_webcam_input_file():
        image_fnames = os.path.join(config["webcam"], '*.jpg')
        images = glob.glob(image_fnames)
        if images:
            images = sorted(images, key=os.path.getmtime, reverse=True)
            puzzle = images[0]
            _assign_puzzle_input_file(puzzle)
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
