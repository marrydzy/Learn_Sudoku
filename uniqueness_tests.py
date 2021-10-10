# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS
    Generally, the Unique Rectangle tests consider four cells that form a rectangle
    whose common candidates are two digits, with one or more of these cells containing
    extra candidates as well. The 4 cells in the corners of the rectangle belong to
    exactly 2 rows, 2 columns and 2 boxes.
    To avoid this deadly pattern, at least one of the extra candidates must be placed.
    In many of the patterns for the Uniqueness Tests, two cells on one side of the rectangle
    (i.e., sharing either the same row or the same column) have only the common two candidate
    digits and no extra candidates. These cells form the floor of the rectangle.
    The other two cells are called the ceiling.

    For descriptions of each of the uniqueness tests see e.g.:
    https://www.learn-sudoku.com/unique-rectangle.html
"""

# 'bi_values' data structure:
# {'xy': {(row, col, box), ...}}


from itertools import combinations
from collections import defaultdict
# from copy import deepcopy

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_BOX, CELL_ROW, CELL_COL, CELLS_IN_BOX, ALL_NBRS
from utils import set_remaining_candidates, eliminate_options, get_stats


def _get_xyz(n_z, board, bi_value, cells_a, cells_b):
    x, y = bi_value
    x_ids = set()
    for id_x in range(9):
        ceiling_conditions = [
            bool(x in board[cells_a[id_x]]),
            bool(y in board[cells_a[id_x]]),
            bool(x in board[cells_b[id_x]]),
            bool(y in board[cells_b[id_x]]),
            bool(2 < len(board[cells_a[id_x]]) <= n_z + 2),
            bool(2 < len(board[cells_b[id_x]]) <= n_z + 2),
            ]
        if all(ceiling_conditions):
            candidates = set(board[cells_a[id_x]]).union(board[cells_b[id_x]])
            if len(candidates) <= n_z + 2:
                x_ids.add(id_x)
    return x_ids


def _get_bi_values_dictionary(board, cells, by_row=True):
    bi_values = defaultdict(set)
    for cell in cells:
        if len(board[cell]) == 2:
            bi_values[board[cell]].add((CELL_ROW[cell] if by_row else CELL_COL[cell],
                                        CELL_COL[cell] if by_row else CELL_ROW[cell],
                                        CELL_BOX[cell]))
    return bi_values


def _get_rectangle(rows, columns):
    in_rows = list(rows)
    in_cols = list(columns)
    return [in_rows[0] * 9 + in_cols[0], in_rows[0] * 9 + in_cols[1],
            in_rows[1] * 9 + in_cols[1], in_rows[1] * 9 + in_cols[0]]


def _get_c_chain(rectangle, bi_value, z_values=None, naked_subset=None):
    chain = defaultdict(set)
    color_1 = 'yellow'
    color_2 = 'lime'
    for node in rectangle:
        chain[node] = {(bi_value[0], color_1), (bi_value[1], color_2)}
        if z_values:
            for digit in z_values:
                chain[node].add((digit, 'cyan'))
        color_1 = 'lime' if color_1 == 'yellow' else 'yellow'
        color_2 = 'lime' if color_2 == 'yellow' else 'yellow'
    if naked_subset:
        for node in naked_subset:
            for digit in z_values:
                chain[node].add((digit, 'cyan'))
    return chain


@get_stats
def test_1(solver_status, board, window):
    """ If there is only one cell in the rectangle that contains extra candidates,
    then the common candidates can be eliminated from that cell.
    Rating: 100
    """

    set_remaining_candidates(board, solver_status)
    bi_values = _get_bi_values_dictionary(board, range(81))
    for bi_value, coordinates in bi_values.items():
        if len(coordinates) > 2:
            for triplet in combinations(coordinates, 3):
                rows = {position[0] for position in triplet}
                columns = {position[1] for position in triplet}
                boxes = {position[2] for position in triplet}
                if len(rows) == 2 and len(columns) == 2 and len(boxes) == 2:
                    rectangle = _get_rectangle(rows, columns)
                    if all(bi_value[0] in board[corner] and bi_value[1] in board[corner] for corner in rectangle):
                        for corner in rectangle:
                            if len(board[corner]) > 2:
                                to_eliminate = {(candidate, corner) for candidate in bi_value}
                                other_candidates = set(board[corner]).difference(bi_value)
                                c_chain = _get_c_chain(rectangle, bi_value, other_candidates)
                                solver_status.capture_baseline(board, window)
                                eliminate_options(solver_status, board, to_eliminate, window)
                                if window:
                                    window.options_visible = window.options_visible.union(rectangle)
                                kwargs = {"solver_tool": "uniqueness_test_1",
                                          "c_chain": c_chain,
                                          "eliminate": to_eliminate, }
                                test_1.clues += len(solver_status.naked_singles)
                                test_1.options_removed += len(to_eliminate)
                                return kwargs
    return None


@get_stats
def test_2(solver_status, board, window):
    """ Suppose both ceiling cells in the rectangle have exactly one extra candidate X.
    Then X can be eliminated from the cells seen by both of these cells.
    Rating: 100
    """

    def _check_rectangles(by_row):
        cells_by_x = CELLS_IN_ROW if by_row else CELLS_IN_COL
        cells_by_y = CELLS_IN_COL if by_row else CELLS_IN_ROW
        for floor_id_x in range(9):
            bi_values = _get_bi_values_dictionary(board, cells_by_x[floor_id_x], by_row)
            for bi_value, coordinates in bi_values.items():
                if len(coordinates) == 2:
                    floor_a = coordinates.pop()
                    floor_b = coordinates.pop()
                    x_ids = _get_xyz(1, board, bi_value, cells_by_y[floor_a[1]], cells_by_y[floor_b[1]])
                    for x_id in x_ids:
                        ceiling_a = x_id * 9 + floor_a[1] if by_row else floor_a[1] * 9 + x_id
                        ceiling_b = x_id * 9 + floor_b[1] if by_row else floor_b[1] * 9 + x_id
                        boxes = {floor_a[2], floor_b[2], CELL_BOX[ceiling_a], CELL_BOX[ceiling_b]}
                        if board[ceiling_a] == board[ceiling_b] and len(boxes) == 2:
                            z_candidate = board[ceiling_a].replace(bi_value[0], '').replace(bi_value[1], '')
                            to_eliminate = set()
                            for cell in set(ALL_NBRS[ceiling_a]).intersection(ALL_NBRS[ceiling_b]):
                                if z_candidate in board[cell]:
                                    to_eliminate.add((z_candidate, cell))
                            if to_eliminate:
                                rows = (floor_a[0], x_id) if by_row else (floor_a[1], floor_b[1])
                                columns = (floor_a[1], floor_b[1]) if by_row else (floor_a[0], x_id)
                                rectangle = _get_rectangle(sorted(rows), sorted(columns))
                                c_chain = _get_c_chain(rectangle, bi_value, {z_candidate, })
                                solver_status.capture_baseline(board, window)
                                eliminate_options(solver_status, board, to_eliminate, window)
                                if window:
                                    window.options_visible = window.options_visible.union(c_chain.keys())
                                kwargs["solver_tool"] = "uniqueness_test_2"
                                kwargs["c_chain"] = c_chain
                                kwargs["impacted_cells"] = {cell for _, cell in to_eliminate}
                                kwargs["eliminate"] = to_eliminate
                                test_2.clues += len(solver_status.naked_singles)
                                test_2.options_removed += len(to_eliminate)
                                return True
        return False

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    if _check_rectangles(True) or _check_rectangles(False):
        return kwargs
    return None


@get_stats
def test_3(solver_status, board, window):
    """ Suppose both ceiling cells have extra candidates.
    By treating these two cells as one node, find k - 1 other cells (as nodes)
    in the same house as these two cells so that the union of the candidates
    for these k cells has exactly k unique digits. Then the Naked Subset rule
    can be applied to eliminate these k digits from the other cells in the house.
    The algorithm is implemented for k = 2, 3 and 4
    Rating: 100
    """

    def find_naked_subset(subset_size, ceiling_a, ceiling_b, bi_value, subset_candidates, by_row):
        search_area = {cell for cell in set(ALL_NBRS[ceiling_a]).intersection(ALL_NBRS[ceiling_b])
                       if len(board[cell]) > 1}
        possible_subset_nodes = {cell for cell in search_area if len(board[cell]) <= subset_size 
                                 and set(board[cell]).intersection(subset_candidates) 
                                 and not set(board[cell]).intersection(bi_value)}
        houses = [possible_subset_nodes.intersection(CELLS_IN_ROW[CELL_ROW[ceiling_a]] if by_row
                                                     else CELLS_IN_COL[CELL_COL[ceiling_a]])]
        if CELL_BOX[ceiling_a] == CELL_BOX[ceiling_b]:
            houses.append(possible_subset_nodes.intersection(CELLS_IN_BOX[CELL_BOX[ceiling_a]]))
        for house in houses:
            for subset_nodes in combinations(house, subset_size-1):
                naked_subset = set("".join(board[cell] for cell in subset_nodes)).union(subset_candidates)
                if len(naked_subset) == subset_size:
                    impacted_cells = search_area
                    for cell in subset_nodes:
                        impacted_cells = impacted_cells.intersection(ALL_NBRS[cell])
                    for cell in impacted_cells:
                        for candidate in naked_subset.intersection(board[cell]):
                            to_eliminate.add((candidate, cell))
                    if to_eliminate:
                        return naked_subset, subset_nodes
        return None, None

    def _check_rectangles(by_row):
        cells_by_x = CELLS_IN_ROW if by_row else CELLS_IN_COL
        cells_by_y = CELLS_IN_COL if by_row else CELLS_IN_ROW

        for floor_id_x in range(9):
            bi_values = _get_bi_values_dictionary(board, cells_by_x[floor_id_x], by_row)
            for bi_value, coordinates in bi_values.items():
                if len(coordinates) == 2:
                    floor_a = coordinates.pop()
                    floor_b = coordinates.pop()
                    for n in (2, 3, 4):
                        x_ids = _get_xyz(n, board, bi_value, cells_by_y[floor_a[1]], cells_by_y[floor_b[1]])
                        for x_id in x_ids:
                            ceiling_a = x_id * 9 + floor_a[1] if by_row else floor_a[1] * 9 + x_id
                            ceiling_b = x_id * 9 + floor_b[1] if by_row else floor_b[1] * 9 + x_id
                            boxes = {floor_a[2], floor_b[2], CELL_BOX[ceiling_a], CELL_BOX[ceiling_b]}
                            if len(boxes) == 2 and board[ceiling_a] != board[ceiling_b]:
                                z_a = board[ceiling_a].replace(bi_value[0], '').replace(bi_value[1], '')
                                z_b = board[ceiling_b].replace(bi_value[0], '').replace(bi_value[1], '')
                                z_ab = set(z_a).union(z_b)
                                naked_subset, subset_nodes = \
                                    find_naked_subset(n, ceiling_a, ceiling_b, bi_value, z_ab, by_row)
                                if to_eliminate:
                                    rows = (floor_a[0], x_id) if by_row else (floor_a[1], floor_b[1])
                                    columns = (floor_a[1], floor_b[1]) if by_row else (floor_a[0], x_id)
                                    rectangle = _get_rectangle(sorted(rows), sorted(columns))
                                    c_chain = _get_c_chain(rectangle, bi_value, naked_subset, subset_nodes)
                                    solver_status.capture_baseline(board, window)
                                    eliminate_options(solver_status, board, to_eliminate, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(c_chain.keys())
                                    kwargs["solver_tool"] = "uniqueness_test_3"
                                    kwargs["c_chain"] = c_chain
                                    kwargs["impacted_cells"] = {cell for _, cell in to_eliminate}
                                    kwargs["eliminate"] = to_eliminate
                                    test_3.clues += len(solver_status.naked_singles)
                                    test_3.options_removed += len(to_eliminate)
                                    return True
        return False

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    to_eliminate = set()
    if _check_rectangles(True) or _check_rectangles(False):
        return kwargs
    return None


@get_stats
def test_4(solver_status, board, window):
    """ Suppose both cells in the ceiling contain extra candidates.
    Suppose the common candidates are U and V, and none of the cells seen by both ceiling cells contains U.
    Then V can be eliminated from these two cells.
    A rectangle that meets this test is also called a Type 4 Unique Rectangle.
    Rating: 100
    """

    def _get_candidate_count(cells, candidate):
        return ''.join(board[cell] for cell in cells).count(candidate)

    def _check_rectangles(by_row):
        cells_by_x = CELLS_IN_ROW if by_row else CELLS_IN_COL
        cells_by_y = CELLS_IN_COL if by_row else CELLS_IN_ROW
        for floor_id_x in range(9):
            bi_values.clear()
            for floor_id_y in range(9):
                cell = cells_by_x[floor_id_x][floor_id_y]
                if len(board[cell]) == 2:
                    bi_values[board[cell]].add((floor_id_x, floor_id_y, CELL_BOX[cell]))
            for bi_value, coordinates in bi_values.items():
                if len(coordinates) == 2:
                    floor_a = coordinates.pop()
                    floor_b = coordinates.pop()
                    x_ids = _get_xyz(7, board, bi_value, cells_by_y[floor_a[1]], cells_by_y[floor_b[1]])
                    for x_id in x_ids:
                        ceiling_a = x_id * 9 + floor_a[1] if by_row else floor_a[1] * 9 + x_id
                        ceiling_b = x_id * 9 + floor_b[1] if by_row else floor_b[1] * 9 + x_id
                        boxes = {floor_a[2], floor_b[2], CELL_BOX[ceiling_a], CELL_BOX[ceiling_b]}
                        if len(boxes) == 2:
                            to_eliminate = None
                            cells = set(ALL_NBRS[ceiling_a]).intersection(ALL_NBRS[ceiling_b])
                            if not _get_candidate_count(cells, bi_value[0]):
                                to_eliminate = {(bi_value[1], ceiling_a), (bi_value[1], ceiling_b)}
                            elif not _get_candidate_count(cells, bi_value[1]):
                                to_eliminate = {(bi_value[0], ceiling_a), (bi_value[0], ceiling_b)}
                            if to_eliminate:
                                rows = (floor_a[0], x_id) if by_row else (floor_a[1], floor_b[1])
                                columns = (floor_a[1], floor_b[1]) if by_row else (floor_a[0], x_id)
                                rectangle = _get_rectangle(sorted(rows), sorted(columns))
                                other_candidates = set(board[ceiling_a]).union(board[ceiling_b]).difference(bi_value)
                                c_chain = _get_c_chain(rectangle, bi_value, other_candidates)
                                solver_status.capture_baseline(board, window)
                                eliminate_options(solver_status, board, to_eliminate, window)
                                if window:
                                    window.options_visible = window.options_visible.union(c_chain.keys()).union(cells)
                                kwargs["solver_tool"] = "uniqueness_test_4"
                                kwargs["c_chain"] = c_chain
                                kwargs["eliminate"] = to_eliminate
                                test_4.clues += len(solver_status.naked_singles)
                                test_4.options_removed += len(to_eliminate)
                                return True
        return False

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    bi_values = defaultdict(set)
    if _check_rectangles(True) or _check_rectangles(False):
        return kwargs
    return None


@get_stats
def test_5(solver_status, board, window):
    """     Suppose exactly two cells in the rectangle have exactly one extra candidate X,
    and both cells are located diagonally across each other in the rectangle.
    Then X can be eliminated from the cells seen by both of these cells.
    This would be called a Type 5 Unique Rectangle.
    Note that in this case the rectangle does not have a floor or ceiling.
    Rating: 100
    """

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    bi_values = _get_bi_values_dictionary(board, range(81))
    bi_values = {key: value for key, value in bi_values.items() if len(value) > 1}
    for bi_value in bi_values:
        for pair in combinations(bi_values[bi_value], 2):
            if pair[0][0] != pair[1][0] and pair[0][1] != pair[1][1] and pair[0][2] != pair[1][2]:
                node_b = pair[0][0] * 9 + pair[1][1]
                node_d = pair[1][0] * 9 + pair[0][1]
                if board[node_b] == board[node_d] and len(set(board[node_b]).difference(bi_value)) == 1:
                    node_a = pair[0][0] * 9 + pair[0][1]
                    node_c = pair[1][0] * 9 + pair[1][1]
                    nodes = [node_a, node_b, node_c, node_d]
                    boxes = {CELL_BOX[node] for node in nodes}
                    if len(boxes) == 2:
                        other_candidates = set(board[node_b]).difference(bi_value)
                        c_chain = _get_c_chain(nodes, bi_value, other_candidates)
                        z_value = other_candidates.pop()
                        to_eliminate = {(z_value, cell) for cell in set(ALL_NBRS[node_b]).intersection(ALL_NBRS[node_d])
                                        if z_value in board[cell]}
                        if to_eliminate:
                            solver_status.capture_baseline(board, window)
                            eliminate_options(solver_status, board, to_eliminate, window)
                            if window:
                                window.options_visible = window.options_visible.union(c_chain.keys())
                            kwargs["solver_tool"] = "uniqueness_test_4"
                            kwargs["c_chain"] = c_chain
                            kwargs["impacted_cells"] = {cell for _, cell in to_eliminate}
                            kwargs["eliminate"] = to_eliminate
                            test_5.clues += len(solver_status.naked_singles)
                            test_5.options_removed += len(to_eliminate)
                            return kwargs
    return None


@get_stats
def test_6(solver_status, board, window):
    """ Suppose exactly two cells in the rectangle contain extra candidates,
    and they are located diagonally across each other in the rectangle.
    Suppose the common candidates are U and V, and none of the other cells
    in the two rows and two columns containing the rectangle contain U.
    Then U can be eliminated from these two cells.
    This is also called a Type 6 Unique Rectangle.
    Rating: 100
    """

    set_remaining_candidates(board, solver_status)
    kwargs = {}
    bi_values = _get_bi_values_dictionary(board, range(81))
    bi_values = {key: value for key, value in bi_values.items() if len(value) > 1}
    for bi_value in bi_values:
        for pair in combinations(bi_values[bi_value], 2):
            if pair[0][0] != pair[1][0] and pair[0][1] != pair[1][1] and pair[0][2] != pair[1][2]:
                node_b = pair[0][0] * 9 + pair[1][1]
                node_d = pair[1][0] * 9 + pair[0][1]
                if len(set(board[node_b]).intersection(bi_value)) == 2 and \
                        len(set(board[node_d]).intersection(bi_value)) == 2:
                    node_a = pair[0][0] * 9 + pair[0][1]
                    node_c = pair[1][0] * 9 + pair[1][1]
                    nodes = [node_a, node_b, node_c, node_d]
                    boxes = {CELL_BOX[node] for node in nodes}
                    if len(boxes) == 2:
                        other_cells = set(CELLS_IN_ROW[pair[0][0]]).union(CELLS_IN_ROW[pair[1][0]]).union(
                            CELLS_IN_COL[pair[0][1]]).union(CELLS_IN_COL[pair[1][1]])
                        other_candidates = ''.join(board[cell] for cell in other_cells)
                        unique_value = None
                        if other_candidates.count(bi_value[0]) == 4:
                            unique_value = bi_value[0]
                        elif other_candidates.count(bi_value[1]) == 4:
                            unique_value = bi_value[1]
                        if unique_value:
                            other_candidates = set(board[node_b]).union(board[node_d]).difference(bi_value)
                            c_chain = _get_c_chain(nodes, bi_value, other_candidates)
                            to_eliminate = {(unique_value, node_b), (unique_value, node_d)}
                            solver_status.capture_baseline(board, window)
                            eliminate_options(solver_status, board, to_eliminate, window)
                            if window:
                                window.options_visible = window.options_visible.union(other_cells)
                            kwargs["solver_tool"] = "uniqueness_test_6"
                            kwargs["c_chain"] = c_chain
                            kwargs["eliminate"] = to_eliminate
                            test_6.clues += len(solver_status.naked_singles)
                            test_6.options_removed += len(to_eliminate)
                            return kwargs
    return None
