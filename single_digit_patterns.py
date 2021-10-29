# -*- coding: UTF-8 -*-

""" 'SUBSETS' CLASS OF SOLVING METHODS

    GLOBAL FUNCTIONS:
        two_string_kite() - '2-String Kite' strategy

    LOCAL FUNCTIONS:
        _get_chain() - returns chain of cells with subset candidates

TODO:

"""

from collections import namedtuple

from utils import CELL_ROW, CELL_COL, CELL_BOX, CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_BOX, SUDOKU_VALUES_LIST
from utils import get_stats, set_remaining_candidates, eliminate_options

ConjugateCells = namedtuple("ConjugatePair", ["cells", "boxes"])
ConjugatePair = namedtuple("ConjugatePair", ["cell_a", "cell_b"])
ErBox = namedtuple("ErBox", ["in_cells", "box", "row", "column"])
BasicErPattern = namedtuple("BasicErPattern", ["candidate", "pattern", "impacted"])


@get_stats
def empty_rectangle(solver_status, board, window):
    """ TODO """

    def get_er_boxes(candidate):
        er_boxes = set()
        for box_id in range(9):
            with_candidate = set(cell for cell in CELLS_IN_BOX[box_id] if candidate in board[cell])
            if len(with_candidate) == 4:
                in_rows = [CELL_ROW[cell] for cell in with_candidate]
                in_columns = [CELL_COL[cell] for cell in with_candidate]
                if len(set(in_rows)) == 3 and len(set(in_columns)) == 3:
                    for row in set(in_rows):
                        if in_rows.count(row) == 2:
                            row_pair = {cell for cell in with_candidate if CELL_ROW[cell] == row}
                            for column in set(in_columns):
                                if in_columns.count(column) == 2:
                                    col_pair = {cell for cell in with_candidate if CELL_COL[cell] == column}
                                    if len(row_pair.union(col_pair)) == 4:
                                        er_boxes.add(ErBox(tuple(with_candidate), box_id, row, column))
        return er_boxes

    def get_conjugate_pairs(candidate, lines):
        conjugate_pairs = set()
        for line in lines:
            in_cells = set(cell for cell in line if candidate in board[cell])
            if len(in_cells) == 2:
                cell_a = in_cells.pop()
                cell_b = in_cells.pop()
                if CELL_BOX[cell_a] != CELL_BOX[cell_b]:
                    conjugate_pairs.add(ConjugatePair(cell_a, cell_b))
        return conjugate_pairs

    def basic_empty_rectangle():
        """ canonical form of empty rectangle pattern """
        for candidate in SUDOKU_VALUES_LIST:
            er_boxes = get_er_boxes(candidate)

            # if er_boxes:
            #     print(f'\tDupa')
            #     return BasicErPattern(candidate, set(er_boxes.pop().in_cells), 0)

            conjugate_pairs = get_conjugate_pairs(candidate, CELLS_IN_ROW)
            for conjugate_pair in conjugate_pairs:
                for er_box in er_boxes:
                    if CELL_COL[conjugate_pair.cell_a] == er_box.column\
                            and CELL_BOX[conjugate_pair.cell_a] != er_box.box:
                        impacted = er_box.row * 9 + CELL_COL[conjugate_pair.cell_b]
                        if candidate in board[impacted]:
                            return BasicErPattern(
                                candidate,
                                set(er_box.in_cells).union({conjugate_pair.cell_a, conjugate_pair.cell_b}),
                                impacted)
                    if CELL_COL[conjugate_pair.cell_b] == er_box.column\
                            and CELL_BOX[conjugate_pair.cell_b] != er_box.box:
                        impacted = er_box.row * 9 + CELL_COL[conjugate_pair.cell_a]
                        if candidate in board[impacted]:
                            return BasicErPattern(
                                candidate,
                                set(er_box.in_cells).union({conjugate_pair.cell_a, conjugate_pair.cell_b}),
                                impacted)
            conjugate_pairs = get_conjugate_pairs(candidate, CELLS_IN_COL)
            for conjugate_pair in conjugate_pairs:
                for er_box in er_boxes:
                    if CELL_ROW[conjugate_pair.cell_a] == er_box.row\
                            and CELL_BOX[conjugate_pair.cell_a] != er_box.box:
                        impacted = CELL_ROW[conjugate_pair.cell_b] * 9 + er_box.column
                        if candidate in board[impacted]:
                            return BasicErPattern(
                                candidate,
                                set(er_box.in_cells).union({conjugate_pair.cell_a, conjugate_pair.cell_b}),
                                impacted)
                    if CELL_ROW[conjugate_pair.cell_b] == er_box.row\
                            and CELL_BOX[conjugate_pair.cell_b] != er_box.box:
                        impacted = CELL_ROW[conjugate_pair.cell_a] * 9 + er_box.column
                        if candidate in board[impacted]:
                            return BasicErPattern(
                                candidate,
                                set(er_box.in_cells).union({conjugate_pair.cell_a, conjugate_pair.cell_b}),
                                impacted)
        return None

    set_remaining_candidates(board, solver_status)
    basic_er_pattern = basic_empty_rectangle()
    if basic_er_pattern:
        kwargs = {}
        to_eliminate = {(basic_er_pattern.candidate, basic_er_pattern.impacted), }
        if window:
            solver_status.capture_baseline(board, window)
        eliminate_options(solver_status, board, to_eliminate, window)
        empty_rectangle.clues += len(solver_status.naked_singles)
        empty_rectangle.options_removed += 1
        kwargs["solver_tool"] = empty_rectangle.__name__
        if window:
            kwargs["chain_a"] = {cell: {(basic_er_pattern.candidate, 'cyan'), } for cell in basic_er_pattern.pattern}
            kwargs["eliminate"] = to_eliminate

        print(f'\t{kwargs["solver_tool"]}')

        return kwargs
    return None


@get_stats
def two_string_kite(solver_status, board, window):
    """ Two crossing strong links, weakly connected in a box """

    def _get_strings(digit, lines):
        strings = set()
        for line in lines:
            cells = tuple(cell for cell in line if digit in board[cell])
            in_boxes = tuple(CELL_BOX[cell] for cell in cells)
            if len(cells) in (2, 3) and len(set(in_boxes)) == 2:
                strings.add(ConjugateCells(cells, in_boxes))
        return strings

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    for candidate in SUDOKU_VALUES_LIST:
        x_strings = _get_strings(candidate, CELLS_IN_ROW)
        y_strings = _get_strings(candidate, CELLS_IN_COL)
        for x_string in x_strings:
            for y_string in y_strings:
                nodes = {cell for cell in x_string.cells}.union(cell for cell in y_string.cells)
                boxes = {box for box in x_string.boxes}.union(box for box in y_string.boxes)
                if len(nodes) == (len(x_string.cells) + len(y_string.cells)) and len(boxes) == 3:
                    end_box_x = boxes.difference(y_string.boxes).pop()
                    end_box_y = boxes.difference(x_string.boxes).pop()
                    if x_string.boxes.count(end_box_x) == 1 and y_string.boxes.count(end_box_y) == 1:
                        end_x = {cell for i, cell in enumerate(x_string.cells) if x_string.boxes[i] == end_box_x}
                        end_y = {cell for i, cell in enumerate(y_string.cells) if y_string.boxes[i] == end_box_y}
                        assert len(end_x) == 1
                        assert len(end_y) == 1
                        end_x = end_x.pop()
                        end_y = end_y.pop()
                        impacted = set(CELLS_IN_COL[CELL_COL[end_x]]).intersection(CELLS_IN_ROW[CELL_ROW[end_y]])
                        assert len(impacted) == 1
                        impacted = impacted.pop()
                        if candidate in board[impacted]:
                            to_eliminate = {(candidate, impacted), }
                            if window:
                                solver_status.capture_baseline(board, window)
                            eliminate_options(solver_status, board, to_eliminate, window)
                            two_string_kite.clues += len(solver_status.naked_singles)
                            two_string_kite.options_removed += 1
                            kwargs["solver_tool"] = two_string_kite.__name__
                            if window:
                                houses = set(CELLS_IN_ROW[CELL_ROW[end_x]]).union(CELLS_IN_COL[CELL_COL[end_y]]).union(
                                    {impacted, })
                                window.options_visible = window.options_visible.union(houses)
                                kwargs["chain_a"] = {cell: {(candidate, 'cyan'), } for cell in nodes}
                                kwargs["eliminate"] = to_eliminate
                                kwargs["house"] = houses
                            return kwargs
    return None
