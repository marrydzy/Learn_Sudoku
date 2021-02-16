# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

import time
import itertools


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


def get_stats(func):
    """ Decorator for getting solver method statistics """
    def function_wrapper(board, window, lone_singles, report_stats):
        if report_stats:
            function_wrapper.calls += 1
            start = time.time()
        ret = func(board, window, lone_singles)
        if report_stats:
            function_wrapper.time_in += time.time() - start
        return ret

    function_wrapper.board_updated = False
    function_wrapper.calls = 0
    function_wrapper.clues = 0
    function_wrapper.options_removed = 0
    function_wrapper.time_in = 0

    return function_wrapper


CELLS_IN_ROW = tuple(tuple(n for n in range(i * 9, (i + 1) * 9)) for i in range(9))
CELLS_IN_COL = tuple(tuple(n for n in range(i, 81, 9)) for i in range(9))
CELLS_IN_SQR = tuple(block_cells(i) for i in range(9))

ALL_NBRS = tuple(neighbour_cells(i) for i in range(81))
SUDOKU_VALUES_LIST = list('123456789')
SUDOKU_VALUES_SET = set('123456789')

CELL_ROW = tuple(i // 9 for i in range(81))
CELL_COL = tuple(i % 9 for i in range(81))
CELL_SQR = tuple((i // 27) * 3 + (i % 9) // 3 for i in range(81))


def manual_solver(board, window, _):
    """ TODO - manual solver """
    print()
    if window:
        for clue in SUDOKU_VALUES_LIST:
            for band in range(3):
                singles = [cell for offset in range(3) for cell in CELLS_IN_COL[3*band+offset] if board[cell] == clue]
                if len(singles) == 2:
                    sqrs = [band + 3*offset for offset in range(3)]
                    sqrs.remove(CELL_SQR[singles[0]])
                    sqrs.remove(CELL_SQR[singles[1]])
                    cells = set(CELLS_IN_SQR[sqrs[0]]) - set(CELLS_IN_COL[CELL_COL[singles[0]]]) \
                            - set(CELLS_IN_COL[CELL_COL[singles[1]]])
                    # print(f'look in {cells = }')
                    clue_cells = [cell for cell in cells if board[cell] == '.']
                    # print(f'clue_cells = {"".join([board[cell] for cell in clue_cells])}')
                    clues = []
                    for cell in clue_cells:
                        values = ''.join([board[i] for i in CELLS_IN_ROW[CELL_ROW[cell]]])
                        # print(f'{values = }')
                        if clue not in values:
                            clues.append(cell)
                    if len(clues) == 1:
                        board[clues[0]] = clue
                        # singles.append(clues[0])
                        print(f'{clue = } in cell = {clues[0]}')
                    window.draw_board(board, "manual_solution", singles=singles, new_clue=clues[0], house=clue_cells)
            for band in range(3):
                singles = [cell for offset in range(3) for cell in CELLS_IN_ROW[3*band+offset] if board[cell] == clue]
                if len(singles) == 2:
                    sqrs = [3*band + offset for offset in range(3)]
                    sqrs.remove(CELL_SQR[singles[0]])
                    sqrs.remove(CELL_SQR[singles[1]])
                    cells = set(CELLS_IN_SQR[sqrs[0]]) - set(CELLS_IN_ROW[CELL_ROW[singles[0]]]) \
                            - set(CELLS_IN_ROW[CELL_ROW[singles[1]]])
                    # print(f'look in {cells = }')
                    clue_cells = [cell for cell in cells if board[cell] == '.']
                    # print(f'clue_cells = {"".join([board[cell] for cell in clue_cells])}')
                    clues = []
                    for cell in clue_cells:
                        values = ''.join([board[i] for i in CELLS_IN_COL[CELL_COL[cell]]])
                        # print(f'{values = }')
                        if clue not in values:
                            clues.append(cell)
                    if len(clues) == 1:
                        print(f'{clue = } in cell = {clues[0]}')
                        board[clues[0]] = clue
                        # singles.append(clues[0])
                        print(f'cell = {clues[0]} board[cell] = {board[clues[0]]}')
                    window.draw_board(board, "manual_solution", singles=singles, new_clue=clues[0], house=clue_cells)

@get_stats
def unique_values(board, window, lone_singles):
    """Identify and mark as solved (add to 'lone singles') cells with
    an unique candidate value in each row, column and block.
    The technique covers Visual Elimination method described in:
    https://www.learn-sudoku.com/visual-elimination.html"""

    def _solve_lone_singles(house):
        unsolved_cells = []
        options = ""
        unsolved_values = SUDOKU_VALUES_SET.copy()
        for cell in house:
            opts = board[cell]
            if len(opts) > 1:
                unsolved_cells.append(cell)
                options += opts
            else:
                unsolved_values.discard(opts)
        if not unsolved_cells:
            return

        found_clues = False
        for option in (value for value in unsolved_values if options.count(value) == 1):
            for cell in unsolved_cells:
                if option in board[cell]:
                    board[cell] = option
                    lone_singles.append(cell)
                    unsolved_cells.remove(cell)
                    unique_values.clues += 1
                    found_clues = True
                    break

        if found_clues:
            unique_values.board_updated = True
            if window:
                window.draw_board(board, "unique_values", singles=lone_singles, house=house)
        return

    if window:
        window.display_info("Hidden Singles")
        window.set_current_board(board)
    unique_values.board_updated = False
    for i in range(9):
        _solve_lone_singles(CELLS_IN_ROW[i])
        _solve_lone_singles(CELLS_IN_COL[i])
        _solve_lone_singles(CELLS_IN_SQR[i])

    return True if unique_values.board_updated else None


@get_stats
def hidden_pairs(board, window, _):
    """A Hidden Pair is basically just a “buried” Naked Pair.
    It occurs when two pencil marks appear in exactly two cells within
    the same house (row, column, or block).
    This technique doesn't solve any cells; instead it reveals Naked Pairs
    by removing other candidates in such cells
    (see https://www.learn-sudoku.com/hidden-pairs.html)
    """

    def _find_pairs(cells):
        values_dic = {}
        pairs_dic = {}
        to_remove = []
        pairs = []

        for cell in cells:
            for value in board[cell]:
                if value in values_dic:
                    values_dic[value].append(cell)
                else:
                    values_dic[value] = [cell]
        for value, in_cells in values_dic.items():
            if len(in_cells) == 2:
                pair = tuple(in_cells)
                if pair in pairs_dic:
                    pairs_dic[pair].append(value)
                else:
                    pairs_dic[pair] = [value]

        for in_cells, values in pairs_dic.items():
            if len(values) == 2:
                options_removed = hidden_pairs.options_removed
                pair = ''.join(values)
                if len(board[in_cells[0]]) > 2:
                    hidden_pairs.options_removed += len(board[in_cells[0]]) - 2
                    board[in_cells[0]] = pair
                if len(board[in_cells[1]]) > 2:
                    hidden_pairs.options_removed += len(board[in_cells[1]]) - 2
                    board[in_cells[1]] = pair
                if hidden_pairs.options_removed > options_removed:
                    hidden_pairs.board_updated = True
                    pairs.append(in_cells[0])
                    pairs.append(in_cells[1])
                    other_options = [value for value in '123456789' if value not in pair]
                    for option in other_options:
                        to_remove.append((option, in_cells[0]))
                        to_remove.append((option, in_cells[1]))
                    if window:
                        window.draw_board(board, "hidden_pairs", remove=to_remove, subset=pairs, house=cells)

    if window:
        window.display_info("Hidden Pairs")
        window.set_current_board(board)
    hidden_pairs.board_updated = False
    for i in range(9):
        _find_pairs(CELLS_IN_ROW[i])
        _find_pairs(CELLS_IN_COL[i])
        _find_pairs(CELLS_IN_SQR[i])
    return True if hidden_pairs.board_updated else None


@get_stats
def naked_twins(board, window, lone_singles):
    """For each 'house' (row, column or square) find twin cells with two options
    and remove the values from the list of candidates (options) of the remaining cells
    (see https://www.learn-sudoku.com/naked-pairs.html)
    """

    def _eliminate_opts(options, cells, to_remove):
        for cell in cells:
            if options[0] in board[cell]:
                to_remove.append((options[0], cell))
                board[cell] = board[cell].replace(options[0], "")
            if options[1] in board[cell]:
                to_remove.append((options[1], cell))
                board[cell] = board[cell].replace(options[1], "")
            if not board[cell]:
                return False
            if len(board[cell]) == 1:
                lone_singles.append(cell)
                naked_twins.clues += 1
        return True

    def _find_pairs(cells):
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        pairs = {}
        for cell in unsolved:
            if len(board[cell]) == 2:
                if board[cell] in pairs:
                    pairs[board[cell]].append(cell)
                else:
                    pairs[board[cell]] = [cell, ]

        for values, in_cells in pairs.items():
            if len(in_cells) > 2:
                return False
            if len(in_cells) == 2:
                to_remove = []
                unsolved.remove(in_cells[0])
                unsolved.remove(in_cells[1])
                if not _eliminate_opts(values, unsolved, to_remove):
                    return False
                if to_remove:
                    naked_twins.options_removed += len(to_remove)
                    naked_twins.board_updated = True
                    if window:
                        window.draw_board(board, "naked_twins", remove=to_remove,
                                          subset=in_cells, house=cells)
        return True

    if window:
        window.display_info("Naked Pairs")
        window.set_current_board(board)
    naked_twins.board_updated = False
    for i in range(9):
        if not _find_pairs(CELLS_IN_ROW[i]):
            break
        if not _find_pairs(CELLS_IN_COL[i]):
            break
        if not _find_pairs(CELLS_IN_SQR[i]):
            break
    else:
        return True if naked_twins.board_updated else None
    return False


@get_stats
def omissions(board, window, lone_singles):
    """For rows and columns:
     - when pencil marks in a row or column are contained within a single block,
       the pencil marks elsewhere in the block can be removed
    For blocks:
     - when pencil marks in a block are in one row or column, the pencil marks
       elsewhere in the row or the column can be removed
    (see: https://www.learn-sudoku.com/omission.html)
    """

    def _in_row_col(cells):
        candidates = SUDOKU_VALUES_SET - {board[cell] for cell in cells if len(board[cell]) == 1}
        if not candidates:
            return True

        unsolved = {cell for cell in cells if len(board[cell]) > 1}
        for value in candidates:
            block = None
            for cell in unsolved:
                if value in board[cell]:
                    if block is None:
                        block = CELL_SQR[cell]
                    elif CELL_SQR[cell] != block:
                        break
            else:
                if block is None or not _prune_block_options(block, value, cells):
                    return False
        return True

    def _prune_block_options(block, value, col_row_cells):
        claims = [(value, cell) for cell in col_row_cells]
        to_remove = []
        other_cells = set(CELLS_IN_SQR[block]) - set(col_row_cells)
        for cell in other_cells:
            if value in board[cell]:
                to_remove.append((value, cell))
                board[cell] = board[cell].replace(value, "")
                if not board[cell]:
                    return False
                if len(board[cell]) == 1:
                    lone_singles.append(cell)
                    omissions.clues += 1
        if to_remove:
            omissions.options_removed += len(to_remove)
            omissions.board_updated = True
            if window:
                window.draw_board(board, "omissions", claims=claims, remove=to_remove,
                                  singles=lone_singles, house=col_row_cells, other_cells=other_cells)
        return True

    def _in_block(cells):
        candidates = SUDOKU_VALUES_SET - {board[cell] for cell in cells if len(board[cell]) == 1}
        if not candidates:
            return True

        unsolved = {cell for cell in cells if len(board[cell]) > 1}
        for value in candidates:
            rows = set()
            cols = set()
            to_remove = []
            for cell in unsolved:
                if value in board[cell]:
                    rows.add(CELL_ROW[cell])
                    cols.add(CELL_COL[cell])
            other_cells = set(CELLS_IN_ROW[rows.pop()]) if len(rows) == 1 else None
            if len(cols) == 1:
                other_cells = other_cells.union(set(CELLS_IN_COL[cols.pop()])) if other_cells else \
                    set(CELLS_IN_COL[cols.pop()])

            if other_cells:
                claims = [(value, cell) for cell in cells]
                other_cells = other_cells - set(cells)
                for cell in other_cells:
                    if value in board[cell]:
                        to_remove.append((value, cell))
                        board[cell] = board[cell].replace(value, "")
                        if not board[cell]:
                            return False
                        if len(board[cell]) == 1:
                            lone_singles.append(cell)
                            omissions.clues += 1
                if to_remove:
                    omissions.options_removed += len(to_remove)
                    omissions.board_updated = True
                    if window:
                        window.draw_board(board, "omissions", claims=claims, remove=to_remove,
                                          singles=lone_singles, house=cells, other_cells=other_cells)
        return True

    if window:
        window.display_info("Omission")
        window.set_current_board(board)
    omissions.board_updated = False
    for i in range(9):
        if not _in_row_col(CELLS_IN_ROW[i]):
            break
        if not _in_row_col(CELLS_IN_COL[i]):
            break
        if not _in_block(CELLS_IN_SQR[i]):
            break
    else:
        return True if omissions.board_updated else None
    return False


@get_stats
def naked_triplets(board, window, lone_singles):
    """Remove candidates (options) using 'naked triplets' technique
    (see https://www.learn-sudoku.com/naked-triplets.html)
    """

    def _find_triplets(cells):
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        if len(unsolved) > 3:
            for triplet in itertools.combinations(unsolved, 3):
                values = set(
                    "".join((board[triplet[0]], board[triplet[1]], board[triplet[2]]))
                )
                if len(values) == 3:
                    to_remove = []
                    if not _reduce_other_cells(values, set(unsolved) - set(triplet), to_remove):
                        return False
                    if to_remove:
                        naked_triplets.options_removed += len(to_remove)
                        naked_triplets.board_updated = True
                        if window:
                            window.draw_board(board, "naked_triplets", remove=to_remove,
                                              subset=triplet, house=cells)
        return True

    def _reduce_other_cells(values, cells, to_remove):
        for cell in cells:
            for value in values:
                if value in board[cell]:
                    to_remove.append((value, cell))
                    board[cell] = board[cell].replace(value, "")
            if not board[cell]:
                return False
            if len(board[cell]) == 1:
                lone_singles.append(cell)
                naked_triplets.clues += 1
        return True

    if window:
        window.display_info("'Naked Triplets' technique")
        window.set_current_board(board)
    naked_triplets.board_updated = False
    for i in range(9):
        if not _find_triplets(CELLS_IN_ROW[i]):
            break
        if not _find_triplets(CELLS_IN_COL[i]):
            break
        if not _find_triplets(CELLS_IN_SQR[i]):
            break
    else:
        return True if naked_triplets.board_updated else None

    return False


@get_stats
def hidden_triplets(board, window, _):
    """When three given pencil marks appear in only three cells
    in any given row, column, or block, all other pencil marks may be removed
    from those cells.
    (see https://www.learn-sudoku.com/hidden-triplets.html)
    """

    def _find_triplets(cells):
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        unique_options = list(set("".join(board[cell] for cell in unsolved)))
        if len(unsolved) < 4 or len(unique_options) < 4:
            return

        options_dic = {}
        # when counting values it is necessary to take into account
        # lone singles as well; because of that the loop is over all cells
        for cell in cells:
            for value in board[cell]:
                if value in options_dic:
                    options_dic[value].append(cell)
                else:
                    options_dic[value] = [cell,]
        for triplet in itertools.combinations(unique_options, 3):
            triplet_cells = []
            for value in triplet:
                triplet_cells.extend(options_dic[value])
            triplet_cells = set(triplet_cells)
            if len(triplet_cells) == 3:
                triplet_values = "".join(board[cell] for cell in triplet_cells)
                to_remove = set(triplet_values) - set(triplet)
                removed = []
                if to_remove:
                    for value in to_remove:
                        for cell in triplet_cells:
                            if value in board[cell]:
                                removed.append((value, cell))
                                board[cell] = board[cell].replace(value, "")
                if removed:
                    hidden_triplets.options_removed += len(removed)
                    hidden_triplets.board_updated = True
                    if window:
                        window.draw_board(board, "hidden_triplets", remove=removed,
                                          subset=triplet_cells, house=cells)

    if window:
        window.display_info("Hidden Triplets")
        window.set_current_board(board)
    hidden_triplets.board_updated = False
    for i in range(9):
        _find_triplets(CELLS_IN_ROW[i])
        _find_triplets(CELLS_IN_COL[i])
        _find_triplets(CELLS_IN_SQR[i])
    return True if hidden_triplets.board_updated else None, 0   # TODE


@get_stats
def hidden_quads(board, window, _):
    """When four given pencil marks appear in only four cells
    in any given row, column, or block, all other pencil marks may be removed
    from those cells.
    (see https://www.learn-sudoku.com/hidden-triplets.html)
    """

    def _find_quads(cells):
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        unique_options = list(set("".join(board[cell] for cell in unsolved)))
        if len(unsolved) < 5 or len(unique_options) < 5:
            return

        options_dic = {}
        # when counting values it is necessary to take into account
        # lone singles as well; because of that the loop is over all cells
        for cell in cells:
            for option in board[cell]:
                if option in options_dic:
                    options_dic[option].append(cell)
                else:
                    options_dic[option] = [cell, ]
        for quad in itertools.combinations(unique_options, 4):
            quad_cells = []
            for value in quad:
                quad_cells.extend(options_dic[value])
            quad_cells = set(quad_cells)
            if len(quad_cells) == 4:
                quad_values = "".join(board[cell] for cell in quad_cells)
                to_remove = []
                for value in set(quad_values) - set(quad):
                    for cell in quad_cells:
                        if value in board[cell]:
                            to_remove.append((value, cell))
                            board[cell] = board[cell].replace(value, "")
                if to_remove:
                    hidden_quads.options_removed += len(to_remove)
                    hidden_quads.board_updated = True
                    if window:
                        window.draw_board(board, "hidden_quads", remove=to_remove,
                                          subset=quad_cells, house=cells)

    if window:
        window.display_info("Hidden Quads")
        window.set_current_board(board)
    hidden_quads.board_updated = False
    for i in range(9):
        _find_quads(CELLS_IN_ROW[i])
        _find_quads(CELLS_IN_COL[i])
        _find_quads(CELLS_IN_SQR[i])
    return True if hidden_quads.board_updated else None


@get_stats
def naked_quads(board, window, lone_singles):
    """Remove candidates (options) using 'naked quads' technique
    (see https://www.learn-sudoku.com/naked-triplets.html)"""

    def _find_quads(cells):
        unsolved = [cell for cell in cells if len(board[cell]) > 1]
        if len(unsolved) > 4:
            for quad in itertools.combinations(unsolved, 4):
                if all((len(board[quad[i]]) > 1 for i in range(4))):
                    to_remove = []
                    values = set(
                        "".join((board[quad[0]], board[quad[1]], board[quad[2]], board[quad[3]])))
                    if len(values) == 4 and not _reduce_other_cells(values, set(unsolved) - set(quad), to_remove):
                        return False
                    # naked_quads.removed += len(to_remove)
                    if to_remove:
                        naked_quads.options_removed += len(to_remove)
                        naked_quads.board_updated = True
                        if window:
                            window.draw_board(board, "naked_quads", remove=to_remove,
                                              subset=quad, house=cells)
        return True

    def _reduce_other_cells(values, cells, to_remove):
        for cell in cells:
            for value in values:
                if value in board[cell]:
                    to_remove.append((value, cell))
                    board[cell] = board[cell].replace(value, "")
            if not board[cell]:
                return False
            if len(board[cell]) == 1:
                lone_singles.append(cell)
                naked_quads.clues += 1
        return True

    # naked_quads.solved = 0
    # naked_quads.removed = 0
    if window:
        window.display_info("Naked Quads")
        window.set_current_board(board)
    naked_quads.board_updated = False
    for i in range(9):
        if not _find_quads(CELLS_IN_ROW[i]):
            break
        if not _find_quads(CELLS_IN_COL[i]):
            break
        if not _find_quads(CELLS_IN_SQR[i]):
            break
    else:
        if naked_quads.board_updated:
            print('\nnaked quads')
        return True if naked_quads.board_updated else None
    return False


@get_stats
def x_wings(board, window, lone_singles):
    """Remove candidates (options) using X Wing technique
    (see https://www.learn-sudoku.com/x-wing.html)"""

    # 'crosses' data structure:
    # {(col_1, col_2): {value: [row_1, ...]}} for 'by row' direction
    # {(row_1, row_2): {value: [col_1, ...]}} for 'by col' direction

    def _find_pairs(direction):
        for i in range(9):
            cells = CELLS_IN_ROW[i] if direction == "by row" else CELLS_IN_COL[i]
            unsolved = [cell for cell in cells if len(board[cell]) > 1]
            options = "".join([board[cell] for cell in unsolved])
            for value in set(options):
                if options.count(value) == 2:
                    in_columns = tuple(j for j in range(9) if value in board[cells[j]])
                    value_pairs = crosses.pop(in_columns, {})
                    if value in value_pairs:
                        value_pairs[value].append(i)
                    else:
                        value_pairs[value] = [i, ]
                    crosses[in_columns] = value_pairs

    def _reduce_opts(other_cells, value):
        for cell in other_cells:
            if value in board[cell]:
                to_remove.append((value, cell))
                board[cell] = board[cell].replace(value, "")
            if not board[cell]:
                return False
            if len(board[cell]) == 1:
                lone_singles.append(cell)
                x_wings.clues += 1
        return True

    crosses = {}
    to_remove = []
    if window:
        window.display_info("X-Wings")
        window.set_current_board(board)
    x_wings.board_updated = False

    _find_pairs("by row")
    for cols, pairs in crosses.items():
        for value, rows in pairs.items():
            if len(rows) == 2:
                to_remove.clear()
                column = [CELLS_IN_COL[cols[0]][i] for i in range(9)
                          if (i not in rows and value in board[CELLS_IN_COL[cols[0]][i]])]
                if column:
                    if not _reduce_opts(column, value):
                        return False
                column = [CELLS_IN_COL[cols[1]][i] for i in range(9)
                          if (i not in rows and value in board[CELLS_IN_COL[cols[1]][i]])]
                if column and not _reduce_opts(column, value):
                    return False
                if to_remove:
                    x_wings.options_removed += len(to_remove)
                    x_wings.board_updated = True
                    if window:
                        corners = [value, rows[0] * 9 + cols[0], rows[0] * 9 + cols[1],
                                   rows[1] * 9 + cols[0], rows[1] * 9 + cols[1]]
                        other_cells = [CELLS_IN_COL[cols[0]][i] for i in range(9) if i not in rows]
                        other_cells.extend([CELLS_IN_COL[cols[1]][i] for i in range(9) if i not in rows])
                        window.draw_board(board, "x_wings", remove=to_remove, singles=lone_singles,
                                          x_wing=corners, subset=[value], other_cells=other_cells)
    crosses.clear()
    _find_pairs("by col")
    for rows, pairs in crosses.items():
        for value, cols in pairs.items():
            if len(cols) == 2:
                to_remove.clear()
                row = [CELLS_IN_ROW[rows[0]][i] for i in range(9)
                       if (i not in cols and value in board[CELLS_IN_ROW[rows[0]][i]])]
                if row and not _reduce_opts(row, value):
                    return False
                row = [CELLS_IN_ROW[rows[1]][i] for i in range(9)
                       if (i not in cols and value in board[CELLS_IN_ROW[rows[1]][i]])]
                if row and not _reduce_opts(row, value):
                    return False
                if to_remove:
                    x_wings.options_removed += len(to_remove)
                    x_wings.board_updated = True
                    if window:
                        corners = [value, rows[0] * 9 + cols[0], rows[0] * 9 + cols[1],
                                   rows[1] * 9 + cols[0], rows[1] * 9 + cols[1]]
                        other_cells = [CELLS_IN_ROW[rows[0]][i] for i in range(9) if i not in cols]
                        other_cells.extend([CELLS_IN_ROW[rows[1]][i] for i in range(9) if i not in cols])
                        window.draw_board(board, "x_wings", remove=to_remove, singles=lone_singles,
                                          x_wing=corners, subset=[value], other_cells=other_cells)
    return True if x_wings.board_updated else None


@get_stats
def y_wings(board, window, lone_singles):
    """Remove candidates (options) using XY Wing technique
    (see https://www.learn-sudoku.com/xy-wing.html)"""

    def _find_wings(cell_id):
        a_value, b_value = board[cell_id]
        corners_ax = {}
        corners_bx = {}
        wings = []
        for nbr_cell in ALL_NBRS[cell_id]:
            if len(board[nbr_cell]) == 2:
                if a_value in board[nbr_cell]:
                    x_value = board[nbr_cell].replace(a_value, "")
                    if x_value in corners_ax:
                        corners_ax[x_value].append(nbr_cell)
                    else:
                        corners_ax[x_value] = [nbr_cell, ]
                elif b_value in board[nbr_cell]:
                    x_value = board[nbr_cell].replace(b_value, "")
                    if x_value in corners_bx:
                        corners_bx[x_value].append(nbr_cell)
                    else:
                        corners_bx[x_value] = [nbr_cell, ]
        for an_x in set(corners_ax) & set(corners_bx):
            for corner_ax in corners_ax[an_x]:
                for corner_bx in corners_bx[an_x]:
                    wings.append((an_x, cell_id, corner_ax, corner_bx))
        return wings

    def _reduce_xs(wings):
        for wing in wings:
            to_remove = []
            for cell_id in set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]]):
                if wing[0] in board[cell_id]:
                    to_remove.append((wing[0], cell_id))
                    board[cell_id] = board[cell_id].replace(wing[0], "")
                    if not board[cell_id]:
                        return False
                    if len(board[cell_id]) == 1:
                        lone_singles.append(cell_id)
                        y_wings.clues += 1
            if to_remove:
                y_wings.options_removed += len(to_remove)
                y_wings.board_updated = True
                if window:
                    window.draw_board(board, "y_wings", y_wing=wing,
                                      singles=lone_singles, remove=to_remove,
                                      other_cells=set(ALL_NBRS[wing[2]]) & set(ALL_NBRS[wing[3]]))

        return True

    if window:
        window.display_info("Y-Wing")
        window.set_current_board(board)
    y_wings.board_updated = False
    for cell in range(81):
        if len(board[cell]) == 2:
            if not _reduce_xs(_find_wings(cell)):
                return False
    return True if y_wings.board_updated else None


@get_stats
def unique_rectangles(board, window, lone_singles):
    """Remove candidates (options) using Unique Rectangle technique
    (see https://www.learn-sudoku.com/unique-rectangle.html)"""

    # 'pairs' data structure:
    # {'xy': [(row, col, blk), ...]}

    # Finding unique rectangles:
    #  - a pair is in at least three cells and the pair values are in options of the fourth one
    #  - the pair is in exactly two rows, to columns and two blocks
    # TODO - the algorithm doesn't work if there are two or more rectangles with the same pair

    def _reduce_rectangle(pair, corners):
        if all(board[corner] == pair for corner in corners):
            return False
        to_remove = []
        for corner in corners:
            if board[corner] != pair:
                subset = [cell for cell in rect if len(board[cell]) == 2]
                if pair[0] in board[corner]:
                    to_remove.append((pair[0], corner))
                    board[corner] = board[corner].replace(pair[0], "")
                if pair[1] in board[corner]:
                    to_remove.append((pair[1], corner))
                    board[corner] = board[corner].replace(pair[1], "")
                if len(board[corner]) == 1:
                    lone_singles.append(corner)
                    unique_rectangles.clues += 1
        if to_remove:
            unique_rectangles.options_removed += len(to_remove)
            unique_rectangles.board_updated = True
            if window:
                kwargs = {"remove": to_remove, "singles": lone_singles,
                          "rectangle": rect, "subset": subset, }
                window.draw_board(board, "unique_rectangles", **kwargs)
                # remove=to_remove, singles=lone_singles, rectangle=rect, subset=subset)
        return True

    if window:
        window.display_info("Unique Rectangle")
        window.set_current_board(board)
    unique_rectangles.board_updated = False
    pairs = {}
    for i in range(81):
        if len(board[i]) == 2:
            if board[i] in pairs:
                pairs[board[i]].append((CELL_ROW[i], CELL_COL[i], CELL_SQR[i]))
            else:
                pairs[board[i]] = [(CELL_ROW[i], CELL_COL[i], CELL_SQR[i]), ]

    for pair, positions in pairs.items():
        if len(positions) > 2:
            rows = list(set(pos[0] for pos in positions))
            cols = list(set(pos[1] for pos in positions))
            blocks = set(pos[2] for pos in positions)
            if len(rows) == 2 and len(cols) == 2 and len(blocks) == 2:
                row_1 = CELLS_IN_ROW[rows[0]]
                row_2 = CELLS_IN_ROW[rows[1]]
                rect = sorted([row_1[cols[0]], row_1[cols[1]], row_2[cols[0]], row_2[cols[1]]])
                for val in pair:
                    if not all(val in board[corner] for corner in rect):
                        break
                else:
                    if not _reduce_rectangle(pair, rect):
                        return False

    return True if unique_rectangles.board_updated else None


@get_stats
def swordfish(board, window, lone_singles):
    """Remove candidates (options) using Swordfish technique
    (see https://www.learn-sudoku.com/x-wing.html)
    """

    def _get_crosses(direction):
        # 'crosses' data structure:
        # {(col_1, col_2): {value: [row_1, ...]}} for 'by row' direction
        # {(row_1, row_2): {value: [col_1, ...]}} for 'by col' direction
        crosses = {}
        for i in range(9):
            cells = CELLS_IN_ROW[i] if direction == "by row" else CELLS_IN_COL[i]
            unsolved = [cell for cell in cells if len(board[cell]) > 1]
            options = "".join([board[cell] for cell in unsolved])
            for value in set(options):
                if options.count(value) == 2:
                    in_columns = tuple(j for j in range(9) if value in board[cells[j]])
                    value_pairs = crosses.pop(in_columns, {})
                    if value in value_pairs:
                        value_pairs[value].append(i)
                    else:
                        value_pairs[value] = [i, ]
                    crosses[in_columns] = value_pairs
        return crosses

    def _reduce_opts(other_cells, value):
        for cell in other_cells:
            if value in board[cell]:
                to_remove.append((value, cell))
                board[cell] = board[cell].replace(value, "")
            if not board[cell]:
                return False
            if len(board[cell]) == 1:
                lone_singles.append(cell)
                swordfish.clues += 1
        return True

    def _find_swordfish(direction):
        crosses = _get_crosses(direction)
        # print(f'\ndirection: {direction}, crosses: {crosses}')
        # 'primary' direction: rows for 'by row' direction, columns otherwise
        # 'secondary' direction: columns for 'by row' direction, rows otherwise
        value_positions = {}
        for secondary_indexes, pairs in crosses.items():
            for value, primary_indexes in pairs.items():
                if len(primary_indexes) == 1:
                    if value in value_positions:
                        value_positions[value].append(
                            (primary_indexes[0], secondary_indexes[0], secondary_indexes[1])
                        )
                    else:
                        value_positions[value] = [
                            (primary_indexes[0], secondary_indexes[0], secondary_indexes[1]),
                        ]
        for value, positions in value_positions.items():
            if len(positions) == 3:
                primary_indexes = []
                secondary_indexes = []
                for position in positions:
                    primary_indexes.append(position[0])
                    secondary_indexes.append(position[1])
                    secondary_indexes.append(position[2])
                in_2_places = (secondary_indexes.count(index) == 2
                               for index in set(secondary_indexes))
                if all(in_2_places):
                    to_remove.clear()
                    sword = [value, ]
                    in_cells = set()    # TODO - change the name
                    for position in positions:
                        if direction == "by row":
                            sword.append(position[0] * 9 + position[1])
                            sword.append(position[0] * 9 + position[2])
                            in_cells = in_cells.union(set(CELLS_IN_COL[position[1]]))
                            in_cells = in_cells.union(set(CELLS_IN_COL[position[2]]))
                        else:
                            sword.append(position[1] * 9 + position[0])
                            sword.append(position[2] * 9 + position[0])
                            in_cells = in_cells.union(set(CELLS_IN_ROW[position[1]]))
                            in_cells = in_cells.union(set(CELLS_IN_ROW[position[2]]))
                    secondary_indexes = set(secondary_indexes)
                    for index in secondary_indexes:
                        if direction == "by row":
                            other_cells = [
                                CELLS_IN_COL[index][row]
                                for row in range(9)
                                if len(board[CELLS_IN_COL[index][row]]) > 1
                                and row not in primary_indexes
                            ]
                        else:
                            other_cells = [
                                CELLS_IN_ROW[index][col]
                                for col in range(9)
                                if len(board[CELLS_IN_ROW[index][col]]) > 1
                                and col not in primary_indexes
                            ]

                        if other_cells and not _reduce_opts(other_cells, value):
                            return False

                    if to_remove:
                        swordfish.options_removed += len(to_remove)
                        swordfish.board_updated = True
                        if window:
                            window.draw_board(board, "swordfish", singles=lone_singles,
                                              sword=sword, remove=to_remove, other_cells=in_cells)
        return True

    to_remove = []
    if window:
        window.display_info("Swordfish")
        window.set_current_board(board)
    swordfish.board_updated = False
    if not _find_swordfish("by row"):
        return False
    if not _find_swordfish("by column"):
        return False
    return True if swordfish.board_updated else None
