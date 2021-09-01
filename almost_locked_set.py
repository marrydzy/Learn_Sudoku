# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from itertools import combinations
from collections import defaultdict

from utils import ALL_NBRS
from utils import get_stats, get_subsets, remove_options


def _get_restricted_commons(als_a, als_b, common_values):
    x_values = set()
    for x in common_values:
        for cell in als_a[x]:
            if als_b[x].intersection(ALL_NBRS[cell]) != als_b[x]:
                break
        else:
            x_values.add(x)
    return x_values


def _get_common_neighbours(cells_a, cells_b, impacted_cells):
    common_neighbours = impacted_cells
    for cell_a in cells_a:
        for cell_b in cells_b:
            common_neighbours = common_neighbours.intersection(ALL_NBRS[cell_a]).intersection(ALL_NBRS[cell_b])
    return common_neighbours


def _get_c_chain(als_a=None, als_b=None, als_c=None, x=None, y=None, z=None):
    chain_a = defaultdict(set)
    chain_b = defaultdict(set)
    chain_c = defaultdict(set)
    als_es = ((als_a, chain_a), (als_b, chain_b), (als_c, chain_c))
    color_x = 'peachpuff'
    color_y = 'lime'
    color_z = 'yellow'
    for als, chain in als_es:
        if als:
            cells = {cell for candidate in als for cell in als[candidate]}
            for cell in cells:
                for candidate in als:
                    if als != als_c and candidate == x:
                        chain[cell].add((candidate, color_x))
                    elif (als != als_b or not als_c) and candidate == y:
                        chain[cell].add((candidate, color_y))
                    elif als != als_a and candidate == z:
                        chain[cell].add((candidate, color_z))
                    elif als != als_c:
                        chain[cell].add((candidate, 'cyan'))
    return chain_a, chain_b, chain_c


def _get_alses(board):
    alses = []
    for n in range(1, 8):
        n_alses = []
        for als in get_subsets(board, n, als=True):
            if als not in n_alses:
                n_alses.append(als)
        alses.extend(n_alses)
    return alses


def _get_alses_with_restricted_common(stem, candidate, alses):
    connected_alses = []
    stem_neighbours = ALL_NBRS[stem]
    for als in alses:
        if candidate in als and als[candidate].intersection(stem_neighbours) == als[candidate]:
            connected_alses.append(als)
    return connected_alses


def _check_if_overlap(als_a, als_b):
    cells_a = {cell for candidate in als_a for cell in als_a[candidate]}
    cells_b = {cell for candidate in als_b for cell in als_b[candidate]}
    return bool(cells_a.intersection(cells_b))


def _select_2_petals(all_petals, stem_candidates):
    for petal_1 in all_petals[stem_candidates[0]]:
        cells_1 = {cell for candidate in petal_1 for cell in petal_1[candidate]}
        for petal_2 in all_petals[stem_candidates[1]]:
            cells_2 = {cell for candidate in petal_2 for cell in petal_2[candidate]}
            blossom_cells = cells_1.union(cells_2)
            petals_lengths = len(cells_1) + len(cells_2)
            if len(blossom_cells) == petals_lengths:
                possible_candidates = set(petal_1).intersection(petal_2)
                possible_candidates = possible_candidates.difference(stem_candidates)
                blossom = {}
                for candidate in possible_candidates:
                    blossom[candidate] = petal_1[candidate].union(petal_2[candidate])
                yield blossom


def _select_3_petals(all_petals, stem_candidates):
    for petal_1 in all_petals[stem_candidates[0]]:
        cells_1 = {cell for candidate in petal_1 for cell in petal_1[candidate]}
        for petal_2 in all_petals[stem_candidates[1]]:
            cells_2 = {cell for candidate in petal_2 for cell in petal_2[candidate]}
            for petal_3 in all_petals[stem_candidates[2]]:
                cells_3 = {cell for candidate in petal_3 for cell in petal_3[candidate]}
                blossom_cells = cells_1.union(cells_2).union(cells_3)
                petals_lengths = len(cells_1) + len(cells_2) + len(cells_3)
                if len(blossom_cells) == petals_lengths:
                    possible_candidates = set(petal_1).intersection(petal_2).intersection(petal_3)
                    possible_candidates = possible_candidates.difference(stem_candidates)
                    blossom = {}
                    for candidate in possible_candidates:
                        blossom[candidate] = petal_1[candidate].union(petal_2[candidate]).union(petal_3[candidate])
                    yield blossom


def _select_4_petals(all_petals, stem_candidates):
    for petal_1 in all_petals[stem_candidates[0]]:
        cells_1 = {cell for candidate in petal_1 for cell in petal_1[candidate]}
        for petal_2 in all_petals[stem_candidates[1]]:
            cells_2 = {cell for candidate in petal_2 for cell in petal_2[candidate]}
            for petal_3 in all_petals[stem_candidates[2]]:
                cells_3 = {cell for candidate in petal_3 for cell in petal_3[candidate]}
                for petal_4 in all_petals[stem_candidates[3]]:
                    cells_4 = {cell for candidate in petal_4 for cell in petal_4[candidate]}
                    blossom_cells = cells_1.union(cells_2).union(cells_3).union(cells_4)
                    petals_lengths = len(cells_1) + len(cells_2) + len(cells_3) + len(cells_4)
                    if len(blossom_cells) == petals_lengths:
                        possible_candidates = set(petal_1).intersection(petal_2).intersection(
                            petal_3).intersection(petal_4)
                        possible_candidates = possible_candidates.difference(stem_candidates)
                        blossom = {}
                        for candidate in possible_candidates:
                            blossom[candidate] = petal_1[candidate].union(petal_2[candidate]).union(
                                petal_3[candidate]).union(petal_4[candidate])
                        yield blossom


@get_stats
def als_xz(solver_status, board, window):
    """  The ALS-XZ rule says that if A and B are Almost Locked Sets (or ALS'es),
    and X is restricted common to A and B, then no other common candidate
    (let's call it Z) can appear outside of A and B in a cell that can see
    all the Z candidates in both A and B.
    Note that it doesn't matter whether or not Z is also restricted common to A and B,
    except that if Z is also restricted common, we can remove X as a candidate
    of any cells outside A and B that can see all the X candidates in both A and B.
    That is, each candidate, in turn, gets to play the role of restricted common,
    giving us the chance to eliminate the other candidate from outside cells.
    Rating: 300-350
    """
    als_es = _get_alses(board)
    for als_a, als_b in combinations(als_es, 2):
        common_values = set(als_a).intersection(als_b)
        cells_a = {cell for candidate in als_a for cell in als_a[candidate]}
        cells_b = {cell for candidate in als_b for cell in als_b[candidate]}
        impacted_cells = {cell for cell in range(81) if len(board[cell]) > 1}.difference(cells_a).difference(cells_b)
        if len(common_values) > 1 and impacted_cells:
            for x in _get_restricted_commons(als_a, als_b, common_values):
                for z in common_values.difference((x,)):
                    common_neighbours = _get_common_neighbours(als_a[z], als_b[z], impacted_cells)
                    if common_neighbours:
                        to_remove = {(z, cell) for cell in common_neighbours if z in board[cell]}
                        if to_remove:
                            chain_a, chain_b, _ = _get_c_chain(als_a=als_a, als_b=als_b, x=z, y=x)
                            solver_status.capture_baseline(board, window)
                            remove_options(solver_status, board, to_remove, window)
                            if window:
                                window.options_visible = window.options_visible.union(cells_a).union(
                                    cells_b).union(common_neighbours)
                            als_xz.rating += 300
                            als_xz.options_removed += len(to_remove)
                            als_xz.clues += len(solver_status.naked_singles)
                            return {"solver_tool": "als_xz",
                                    "chain_a": chain_a,
                                    "chain_b": chain_b,
                                    "remove": to_remove,
                                    "impacted_cells": {cell for _, cell in to_remove}, }
    return None


@get_stats
def als_xy_wing(solver_status, board, window):
    """  Say we have three Almost Locked Sets A, B and C.
    Suppose:
        A and C share a restricted common Y,
        B and C share a restricted common Z, and
        Y and Z are different digits.
    Then for any digit X that is distinct from Y and Z and is a common candidate for A and B,
    we can eliminate X from any cell that sees all cells belonging to either A or B and having X as a candidate.
    Rating: 320-350
    """
    als_es = _get_alses(board)
    als_cells = {}
    unresolved = {cell for cell in range(81) if len(board[cell]) > 1}
    for idx_0, idx_1, idx_2 in combinations(range(len(als_es)), 3):
        common_values = set(als_es[idx_0]).intersection(als_es[idx_1]).intersection(als_es[idx_2])
        if not common_values:
            continue
        if idx_0 not in als_cells:
            als_cells[idx_0] = {cell for candidate in als_es[idx_0] for cell in als_es[idx_0][candidate]}
        if idx_1 not in als_cells:
            als_cells[idx_1] = {cell for candidate in als_es[idx_1] for cell in als_es[idx_1][candidate]}
        if idx_2 not in als_cells:
            als_cells[idx_2] = {cell for candidate in als_es[idx_2] for cell in als_es[idx_2][candidate]}
        for idx_a, idx_b, idx_c in ((idx_0, idx_1, idx_2), (idx_1, idx_2, idx_0), (idx_0, idx_2, idx_1)):
            als_a = als_es[idx_a]
            cells_a = als_cells[idx_a]
            als_b = als_es[idx_b]
            cells_b = als_cells[idx_b]
            als_c = als_es[idx_c]
            cells_c = als_cells[idx_c]
            impacted_cells = unresolved.difference(cells_a).difference(cells_b)
            if impacted_cells:
                for y in _get_restricted_commons(als_a, als_c, set(als_a).intersection(als_c)):
                    for z in _get_restricted_commons(als_b, als_c, set(als_b).intersection(als_c)):
                        if y != z:
                            for x in set(als_a).intersection(als_b).difference({y, z}):
                                common_neighbours = _get_common_neighbours(als_a[x], als_b[x], impacted_cells)
                                if common_neighbours:
                                    to_remove = {(x, cell) for cell in common_neighbours if x in board[cell]}
                                    if to_remove:
                                        chain_a, chain_b, chain_c = _get_c_chain(als_a=als_a, als_b=als_b, als_c=als_c,
                                                                                 x=x, y=y, z=z)
                                        impacted_cells = {cell for _, cell in to_remove}.difference(
                                            cells_a).difference(cells_b).difference(cells_c)
                                        solver_status.capture_baseline(board, window)
                                        remove_options(solver_status, board, to_remove, window)
                                        if window:
                                            window.options_visible = window.options_visible.union(cells_a).union(
                                                cells_b).union(cells_c).union(common_neighbours)
                                        als_xy_wing.rating += 330
                                        als_xy_wing.options_removed += len(to_remove)
                                        als_xy_wing.clues += len(solver_status.naked_singles)
                                        return {"solver_tool": "als_xy_wing",
                                                "chain_a": chain_a,
                                                "chain_b": chain_b,
                                                "chain_c": chain_c,
                                                "remove": to_remove,
                                                "impacted_cells": impacted_cells,
                                                }
    return None


@get_stats
def death_blossom(solver_status, board, window):
    """
    Rating: 360
    """

    unresolved = {cell for cell in range(81) if len(board[cell]) > 1}
    als_es = _get_alses(board)
    for stem_size in (2, 3, 4):
        stems = {cell for cell in range(81) if len(board[cell]) == stem_size}
        for stem in stems:
            all_petals = {}
            for candidate in board[stem]:
                candidate_petals = _get_alses_with_restricted_common(stem, candidate, als_es)
                if candidate_petals:
                    all_petals[candidate] = candidate_petals
            if len(all_petals) == len(board[stem]):
                stem_candidates = board[stem]
                for blossom in _select_2_petals(all_petals, stem_candidates) if stem_size == 2 \
                        else (_select_3_petals(all_petals, stem_candidates) if stem_size == 3
                              else _select_4_petals(all_petals, stem_candidates)):
                    blossom_cells = {cell for petal in blossom for cell in petal}
                    impacted_cells = unresolved.difference(blossom_cells)
                    possible_candidates = set(blossom)
                    to_remove = set()
                    for cell in impacted_cells:
                        if possible_candidates.intersection(board[cell]):
                            cell_neighbours = set(ALL_NBRS[cell])
                            for candidate in possible_candidates.intersection(board[cell]):
                                candidate_cells = blossom[candidate]
                                if candidate_cells.intersection(cell_neighbours) == candidate_cells:
                                    to_remove.add((candidate, cell))
                    if to_remove:
                        solver_status.capture_baseline(board, window)
                        remove_options(solver_status, board, to_remove, window)
                        if window:
                            window.options_visible = window.options_visible.union(blossom_cells)
                        # print('\tDeath Blossom')
                        return {"solver_tool": "death_blossom",
                                "remove": to_remove, }
    return None


@get_stats
def als_xy(solver_status, board, window):
    """  TODO
    Rating: 300
    """
    als_es = _get_alses(board)
    for als_a, als_b in combinations(als_es, 2):
        if _check_if_overlap(als_a, als_b):
            continue
        common_values = set(als_a).intersection(als_b)
        impacted_cells = {cell for cell in range(81) if len(board[cell]) > 1}.difference(als_a).difference(als_b)
        if len(common_values) > 1 and impacted_cells:
            restricted_commons = _get_restricted_commons(als_a, als_b, common_values)
            if len(restricted_commons) == 2:
                to_remove = set()
                x = list(restricted_commons)[0]
                y = list(restricted_commons)[1]
                for cell in impacted_cells:
                    if x in board[cell] and set(ALL_NBRS[cell]).intersection(als_a[x]) == als_a[x] and \
                            set(ALL_NBRS[cell]).intersection(als_b[x]) == als_b[x]:
                        to_remove.add((x, cell))
                    if y in board[cell] and set(ALL_NBRS[cell]).intersection(als_a[y]) == als_a[y] and \
                            set(ALL_NBRS[cell]).intersection(als_b[y]) == als_b[y]:
                        to_remove.add((y, cell))
                # if to_remove:
                #     print('\tBingo!')
                for z in set(als_a).difference(restricted_commons):
                    for cell in impacted_cells:
                        if z in board[cell] and set(ALL_NBRS[cell]).intersection(als_a[z]) == als_a[z]:
                            to_remove.add((z, cell))
                for z in set(als_b).difference(restricted_commons):
                    for cell in impacted_cells:
                        if z in board[cell] and set(ALL_NBRS[cell]).intersection(als_b[z]) == als_b[z]:
                            to_remove.add((z, cell))
                if to_remove:
                    cells_a = {cell for candidate in als_a for cell in als_a[candidate]}
                    cells_b = {cell for candidate in als_b for cell in als_b[candidate]}
                    c_chain, d_chain, _ = _get_c_chain(als_a=als_a, als_b=als_b,
                                                       x=restricted_commons.pop(), z=restricted_commons.pop())
                    solver_status.capture_baseline(board, window)
                    remove_options(solver_status, board, to_remove, window)
                    if window:
                        window.options_visible = window.options_visible.union(cells_a).union(
                            cells_b).union(impacted_cells)
                    # print(f'\n{cells_a = }, \n{cells_b = }, \n{restricted_commons = }')
                    als_xy.rating += 320
                    als_xy.options_removed += len(to_remove)
                    als_xy.clues += len(solver_status.naked_singles)
                    return {"solver_tool": "als_xy",
                            "chain_a": c_chain,
                            "chain_b": d_chain,
                            "remove": to_remove,
                            "impacted_cells": {cell for _, cell in to_remove
                                               if cell not in cells_a.union(cells_b)}, }
    return None
