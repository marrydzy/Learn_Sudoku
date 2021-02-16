# -*- coding: UTF-8 -*-

""" Utilities related to input files """

import os
import sys
import glob
import difflib
from pathlib import Path
from display import error_message, did_you_mean_message


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
