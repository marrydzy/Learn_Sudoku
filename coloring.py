# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from collections import defaultdict
from itertools import combinations

import networkx as nx

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import is_clue, init_options, remove_options


def _get_strongly_connected_cells(board, solver_status):
    """ Return dictionary of strongly connected cells
    connected_cells data format:
    {(cell_1, cell_2): {candidate_1, candidate_2, ...}, ...} """

    def _add_connected(cells):
        unsolved_cells = [cell for cell in cells if not is_clue(cell, board, solver_status)]
        if unsolved_cells:
            candidates = ''.join(board[cell] for cell in unsolved_cells)
            for value in SUDOKU_VALUES_LIST:
                if candidates.count(value) == 2:
                    cells_pair = tuple([cell for cell in unsolved_cells if value in board[cell]])
                    connected_cells[cells_pair].add(value)

    connected_cells = defaultdict(set)
    for indx in range(9):
        _add_connected(CELLS_IN_ROW[indx])
        _add_connected(CELLS_IN_COL[indx])
        _add_connected(CELLS_IN_SQR[indx])
    return connected_cells


def _get_pair_house(pair):
    """ Return house of the cells pair """
    cell_a, cell_b = pair
    if CELL_ROW[cell_a] == CELL_ROW[cell_b]:
        return CELLS_IN_ROW[CELL_ROW[cell_a]]
    if CELL_COL[cell_a] == CELL_COL[cell_b]:
        return CELLS_IN_COL[CELL_COL[cell_a]]
    return CELLS_IN_SQR[CELL_SQR[cell_a]]


def _get_graph_houses(edges):
    """ Return complete set of houses of graph edges """
    houses = set()
    for edge in edges:
        houses = houses.union(_get_pair_house(edge))
    return houses


# single-digit techniques utility functions:

def _build_graph(value, board, solver_status):
    def _for_house(cells):
        nodes = [cell for cell in cells if
                 value in board[cell] and not is_clue(cell, board, solver_status)]
        if len(nodes) == 2:
            graph.add_edge(nodes[0], nodes[1])

    graph = nx.Graph()
    for i in range(9):
        _for_house(CELLS_IN_ROW[i])
        _for_house(CELLS_IN_COL[i])
        _for_house(CELLS_IN_SQR[i])
    return graph


def _get_c_chain(graph, component, value, colors=('lime', 'yellow')):
    c_chain = {node: set() for node in component}
    node = list(component)[0]
    _paint_node(graph, component, c_chain, node, value, colors, 0)
    return c_chain


def _paint_node(graph, component, c_chain, node, value, colors, color_id):
    if node not in component or (value, colors[color_id]) in c_chain[node]:
        return
    c_chain[node].add((value, colors[color_id]))
    color_id = (color_id + 1) % 2
    for neighbour_node in graph.adj[node]:
        _paint_node(graph, component, c_chain, neighbour_node, value, colors, color_id)


def _get_chain_colors(c_chain):
    return {color for node in c_chain for _, color in c_chain[node]}


def _get_value_color_nodes(c_chain, value, color):
    return {node for node in c_chain if (value, color) in c_chain[node]}


# XXXXX

def _check_bidirectional_traversing(end_value, path, board):
    def _traverse(nodes):
        exp_value = end_value
        for node in nodes:
            exp_value = board[node].replace(exp_value, '')
            if len(exp_value) != 1:
                return False
        return True if exp_value == end_value else False

    if len(path) < 3:
        return False
    return _traverse(path) and _traverse(path[-1::-1])


def _try_value(board, node, value):
    if value not in board[node]:
        return False
    board[node] = value
    for impacted_cell in ALL_NBRS[node]:
        board[impacted_cell] = board[impacted_cell].replace(value, '')
        if not board[impacted_cell]:
            return False
    return True


def _walk(board, graph, path, start_node, start_value, end_node, end_value):
    """ walks possible paths between start_node and end_node,
    starting with start value
    Returns:
        True if the only value in end_node can be end_value,
        False otherwise
    """

    current_node = start_node
    current_value = start_value
    while current_node != end_node:
        if not _try_value(board, current_node, current_value):
            return
        path.append(current_node)

        next_nodes = set(graph.adj[current_node]).difference(set(path))
        if not next_nodes:
            return
        elif len(next_nodes) == 1:
            next_node = next_nodes.pop()
            edge_values = set(graph.edges[(current_node, next_node)]['candidates'])
            edge_values.discard(current_value)
            if not edge_values:
                return
            assert(len(edge_values) == 1)
            current_node = next_node
            current_value = edge_values.pop()

        else:
            for next_node in next_nodes:
                edge_values = set(graph.edges[(current_node, next_node)]['candidates'])
                edge_values.discard(current_value)
                if edge_values:
                    assert (len(edge_values) == 1)
                    _walk(board.copy(), graph, path.copy(), next_node, edge_values.pop(), end_node, end_value)
            return
    path.append(current_node)
    if current_value == end_value:
        edge_1 = (path[-2], path[-1])
        edge_2 = (path[1], path[2])
        if end_value in graph.edges[edge_1]['candidates']:
            if end_value in graph.edges[edge_2]['candidates']:
                hidden_xy_chain.paths.append(path.copy())
    else:
        hidden_xy_chain.failures += 1


def _color_hidden_xy_chain(graph, path, end_value):
    """ Color candidates of strongly connected cells in Hidden XY Chain:
        - with 'c' color (CYAN) for the first and last edge in the chain
        - alternately with 'g' (LIME) or 'y' (YELLOW) for inner edges of the chain
    Input Data format:
        graph: nx.graph
        path: list of chain nodes
        end_value: candiate value in the first and last chain node
    Returns:
        c_chain: dictionary of chain nodes with set of (option, color) pairs as their values
    """
    xy_chain = defaultdict(set)
    xy_chain[path[0]].add((end_value, 'cyan'))
    xy_chain[path[-1]].add((end_value, 'cyan'))
    for idx in range(len(path) - 1):
        colors_used = {value: color for value, color in xy_chain[path[idx]]}
        colors_available = [color for color in ('lime', 'yellow', 'magenta', 'aqua', 'moccasin')
                            if color not in colors_used.values()]
        edge = (path[idx], path[idx+1])
        candidates = graph.edges[edge]['candidates']
        for candidate in candidates:
            if candidate in colors_used:
                color = colors_used[candidate]
            else:
                color = colors_available[0]
                colors_available = colors_available[1:]
            if idx + 2 == len(path) and candidate == end_value:
                color = 'cyan'
            xy_chain[path[idx]].add((candidate, color))
            xy_chain[path[idx+1]].add((candidate, color))
    return xy_chain


def _color_naked_xy_chain(graph, path, end_value):
    """ Color candidates of strongly connected cells forming a chain:
        - the common candidate in the first and last node of the chain with 'cyan'
        - strongly connected candidates subsequently with 'lime', 'yellow', and 'moccasin' colors
    Input Data format:
        graph: nx.graph
        path: list of chain nodes
        end_value: common candidate value in the first and last chain node
    Returns:
        c_chain: dictionary of chain nodes with set of (option, color) pairs as their values
    """
    c_chain = defaultdict(set)
    c_chain[path[0]].add((end_value, 'cyan'))
    c_chain[path[-1]].add((end_value, 'cyan'))
    colors = ('lime', 'yellow', 'moccasin')
    color_idx = 0
    for node_idx in range(len(path)-1):
        edge = (path[node_idx], path[node_idx+1])
        values = graph.edges[edge]['candidates']
        assert(len(values) == 1)
        value_color_pair = (values.pop(), colors[color_idx])
        c_chain[path[node_idx]].add(value_color_pair)
        c_chain[path[node_idx+1]].add(value_color_pair)
        color_idx = (color_idx + 1) % 3
    return c_chain


def hidden_xy_chain(solver_status, board, window):
    """ TODO """

    connected_cells = _get_strongly_connected_cells(board, solver_status)
    graph = nx.Graph()
    for edge, candidates in connected_cells.items():
        graph.add_edge(*edge, candidates=candidates)

    unresolved = [cell for cell in range(81) if len(board[cell]) > 2]
    kwargs = {}

    for cell in unresolved:
        for candidate in board[cell]:
            hidden_xy_chain.paths = []
            hidden_xy_chain.failures = 0
            ends = set()
            nodes = set(ALL_NBRS[cell])
            for node_1, node_2, candidates in graph.edges.data('candidates'):
                if candidate in candidates:
                    if node_1 in nodes:
                        ends.add(node_1)
                    if node_2 in nodes:
                        ends.add(node_2)
            if len(ends) == 2:
                ends = list(ends)
                for start_node in ends:
                    end_node = ends[1] if start_node == ends[0] else ends[0]
                    start_values = board[start_node].replace(candidate, '')
                    for start_value in start_values:
                        visited_nodes = [cell, ]
                        _walk(board.copy(), graph, visited_nodes, start_node, start_value, end_node, candidate)

                path = []
                min_length = 100
                for p in hidden_xy_chain.paths:
                    min_length = len(p) if len(p) < min_length else min_length
                for p in hidden_xy_chain.paths:
                    if len(p) == min_length:
                        # print(p)
                        path = p
                        break
                if path and hidden_xy_chain.failures == 0:
                    path = path[1:]
                    impacted_cells = {cell for cell in set(ALL_NBRS[path[0]]).intersection(set(ALL_NBRS[path[-1]]))
                                      if not is_clue(cell, board, solver_status)}
                    to_remove = [(candidate, cell) for cell in impacted_cells if candidate in board[cell]]
                    solver_status.capture_baseline(board, window)
                    if window:
                        window.options_visible = window.options_visible.union(set(path)).union({cell})
                    remove_options(solver_status, board, to_remove, window)
                    kwargs["solver_tool"] = "hidden_xy_chain"
                    kwargs["impacted_cells"] = impacted_cells
                    kwargs["remove"] = to_remove
                    kwargs["c_chain"] = _color_hidden_xy_chain(graph, path, candidate)
                    return kwargs

    return kwargs


def naked_xy_chain(solver_status, board, window):
    """ Remove candidates (options) using XY Wing technique:
    For explanation of the technique see e.g.:
     - http://www.sudokusnake.com/nakedxychains.php
    The strategy is assessed as 'Hard', 'Unfair', or 'Diabolical'.
    Ranking of the method (called XY-Chain) varies widely
    260 and 900
    Implementation comments:
    Building a graph and identifying potential chains (paths) was straightforward.
    A slightly tricky part was to add checking for possibility of bidirectional traversing
    between end nodes of the potential paths
    """

    def _build_bi_value_cells_graph():
        bi_value_cells = set(cell for cell in range(81) if len(board[cell]) == 2)
        graph = nx.Graph()
        for cell in bi_value_cells:
            neighbours = set(ALL_NBRS[cell]).intersection(bi_value_cells)
            graph.add_edges_from(
                [(cell, other_cell, {'candidates': set(board[cell]).intersection(set(board[other_cell]))})
                 for other_cell in neighbours if len(set(board[cell]).intersection(set(board[other_cell]))) == 1])
        return graph

    graph = _build_bi_value_cells_graph()
    components = list(nx.connected_components(graph))
    unresolved = [cell for cell in range(81) if len(board[cell]) > 2]
    kwargs = {}
    for cell in unresolved:
        for component in components:
            nodes = component.intersection(set(ALL_NBRS[cell]))
            candidates = ''.join(board[node] for node in nodes)
            for candidate in board[cell]:
                if candidates.count(candidate) == 2:
                    ends = [node for node in nodes if candidate in board[node]]
                    path = nx.algorithms.shortest_paths.generic.shortest_path(graph, ends[0], ends[1])
                    if _check_bidirectional_traversing(candidate, path, board):
                        impacted_cells = {cell for cell in set(ALL_NBRS[path[0]]).intersection(set(ALL_NBRS[path[-1]]))
                                          if not is_clue(cell, board, solver_status)}
                        to_remove = [(candidate, cell) for cell in impacted_cells if candidate in board[cell]]
                        edges = [(path[n], path[n+1]) for n in range(len(path)-1)]
                        solver_status.capture_baseline(board, window)
                        if window:
                            window.options_visible = window.options_visible.union(
                                _get_graph_houses(edges)).union({cell})
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "naked_xy_chain"
                        kwargs["impacted_cells"] = impacted_cells
                        kwargs["remove"] = to_remove
                        kwargs["c_chain"] = _color_naked_xy_chain(graph, path, candidate)
                        kwargs["edges"] = edges
                        return kwargs
    return kwargs


def simple_colors(solver_status, board, window):
    """ Clear description of the technique is available at:
    https://www.sudoku9981.com/sudoku-solving/simple-colors.php
    The technique includes two strategies called:
    Color Trap (https://www.sudoku9981.com/sudoku-solving/color-trap.php), and
    Color Wrap (https://www.sudoku9981.com/sudoku-solving/color-wrap.php
     Ranking of the methods is at the level of 200 ('Hard')
    """

    def _color_trap():
        """ two chain cells with different color are pointing at another cell
        outside of the chain that has a candidate equal to the value """
        impacted_cells = [cell for cell in range(81) if cell not in component and value in board[cell]
                          and not is_clue(cell, board, solver_status)]
        to_remove = []
        for cell in impacted_cells:
            impacting_chain_nodes = component.intersection(set(ALL_NBRS[cell]))
            web_nodes_colors = set(pair[1] for node in impacting_chain_nodes for pair in c_chain[node])
            if len(web_nodes_colors) > 1:
                assert(len(web_nodes_colors) == 2)
                to_remove.append((value, cell))
        if to_remove:
            edges = [edge for edge in graph.edges if edge[0] in component]
            solver_status.capture_baseline(board, window)
            if window:
                window.options_visible = window.options_visible.union(_get_graph_houses(edges))
            remove_options(solver_status, board, to_remove, window)
            kwargs["solver_tool"] = "color trap"
            kwargs["c_chain"] = c_chain
            kwargs["edges"] = edges
            kwargs["remove"] = to_remove
            kwargs["impacted_cells"] = [pair[1] for pair in to_remove]
            return True
        return False

    def _color_wrap():
        """ If in any house (row, column, box) there are two chain cells
         with the same color assigned to a value, then the value can be removed from all cells
         where it is marked with that color """

        conflicted_cells = set()
        conflicting_color = set()

        def _check_houses(houses):
            impacted_nodes = conflicted_cells
            impacting_color = conflicting_color
            for i in range(9):
                house_nodes = component.intersection(houses[i])
                if len(house_nodes) > 1:
                    colors = set(pair[1] for node in house_nodes for pair in c_chain[node])
                    if len(colors) == 1:
                        impacted_nodes = impacted_nodes.union(house_nodes)
                        impacting_color = impacting_color.union(colors)
                    elif len(house_nodes) > 2:
                        assert(len(colors) == 2)
                        nodes_with_color = defaultdict(set)
                        for node in house_nodes:
                            assert(len(c_chain[node]) == 1)
                            vc_pair = c_chain[node].pop()
                            c_chain[node].add(vc_pair)
                            nodes_with_color[vc_pair[1]].add(node)
                        for color in nodes_with_color:
                            if len(nodes_with_color[color]) > 1:
                                impacted_nodes = impacted_nodes.union(nodes_with_color[color])
                                impacting_color.add(color)
            return impacted_nodes, impacting_color

        conflicted_cells, conflicting_color = _check_houses(CELLS_IN_ROW)
        conflicted_cells, conflicting_color = _check_houses(CELLS_IN_COL)
        conflicted_cells, conflicting_color = _check_houses(CELLS_IN_SQR)

        if conflicted_cells:
            assert(len(conflicting_color) == 1)
            conflicting_color = conflicting_color.pop()
            in_conflict = {(value, node) for node in conflicted_cells}
            to_remove = {(value, node) for node in component if (value, conflicting_color) in c_chain[node]}
            impacted_cells = {node for node in component if (value, conflicting_color) in c_chain[node]}
            edges = [edge for edge in graph.edges if edge[0] in component]
            solver_status.capture_baseline(board, window)
            if window:
                window.options_visible = window.options_visible.union(_get_graph_houses(edges))
            remove_options(solver_status, board, to_remove, window)
            kwargs["solver_tool"] = "color wrap"
            kwargs["c_chain"] = {node: c_chain[node] for node in component.difference(impacted_cells)}
            kwargs["edges"] = edges
            kwargs["remove"] = to_remove
            kwargs["impacted_cells"] = impacted_cells
            kwargs["conflicting_cells"] = in_conflict
            return True
        return False

    kwargs = {}
    for value in SUDOKU_VALUES_LIST:
        graph = _build_graph(value, board, solver_status)
        for component in list(nx.connected_components(graph)):
            c_chain = _get_c_chain(graph, component, value)
            if _color_wrap():
                return kwargs
            if _color_trap():
                return kwargs
    return kwargs


def multi_colors(solver_status, board, window):
    """ TODO """

    def _check_components(component_ids):
        components = [all_components[component_ids[0]], all_components[component_ids[1]]]
        c_chains = [_get_c_chain(graph, components[0], value, colors=('lime', 'yellow')),
                    _get_c_chain(graph, components[1], value, colors=('aqua', 'violet'))]
        if len(c_chains[0]) and len(c_chains[1]):
            if _find_color_wing(components, c_chains, m_id=0, s_id=1):
                return True
            if _find_color_wing(components, c_chains, m_id=1, s_id=0):
                return True
            if _find_color_trap(components, c_chains):
                return True
        return False

    def _find_color_wing(components, c_chains, m_id, s_id):
        colors = list(_get_chain_colors(c_chains[m_id]))
        color_nodes = [_get_value_color_nodes(c_chains[m_id], value, colors[0]),
                       _get_value_color_nodes(c_chains[m_id], value, colors[1])]
        edges = {edge for edge in graph.edges if edge[0] in components[s_id]}
        for edge in edges:
            for col_id in (0, 1):
                see_color_nodes_a = color_nodes[col_id].intersection(ALL_NBRS[edge[0]])
                see_color_nodes_b = color_nodes[col_id].intersection(ALL_NBRS[edge[1]])
                if see_color_nodes_a and see_color_nodes_b:
                    conflicting_color = colors[col_id]
                    conflicted_cells = see_color_nodes_a.union(see_color_nodes_b)
                    impacted_cells = {node for node in components[m_id]
                                      if (value, conflicting_color) in c_chains[m_id][node]}
                    to_remove = {(value, node) for node in impacted_cells}
                    in_conflict = {(value, node) for node in conflicted_cells}
                    edges = [edge for edge in graph.edges
                             if edge[0] in components[m_id].union(components[s_id])]
                    solver_status.capture_baseline(board, window)
                    if window:
                        window.options_visible = window.options_visible.union(_get_graph_houses(edges))
                    remove_options(solver_status, board, to_remove, window)
                    c_chain = {**c_chains[m_id], **c_chains[s_id]}
                    kwargs["solver_tool"] = "multi_colors"
                    kwargs["c_chain"] = {node: c_chain[node] for node
                                         in components[m_id].union(components[s_id]).difference(impacted_cells)}
                    kwargs["edges"] = edges
                    kwargs["remove"] = to_remove
                    kwargs["impacted_cells"] = impacted_cells
                    kwargs["conflicting_cells"] = in_conflict
                    # print('\nmulti colors - color wing')
                    return True
        return False

    def _find_color_trap(components, c_chains):
        colors = [list({val_col_pair[1] for node in components[0] for val_col_pair in c_chains[0][node]}),
                  list({val_col_pair[1] for node in components[1] for val_col_pair in c_chains[1][node]})]
        color_nodes = [{node for node in components[0] if c_chains[0][node] == {(value, colors[0][0])}},
                       {node for node in components[0] if c_chains[0][node] == {(value, colors[0][1])}},
                       {node for node in components[1] if c_chains[1][node] == {(value, colors[1][0])}},
                       {node for node in components[1] if c_chains[1][node] == {(value, colors[1][1])}}]
        impacting_subsets = None
        for node in color_nodes[0]:
            if color_nodes[2].intersection(ALL_NBRS[node]):
                impacting_subsets = (color_nodes[1], color_nodes[3])
                break
            if color_nodes[3].intersection(ALL_NBRS[node]):
                impacting_subsets = (color_nodes[1], color_nodes[2])
                break
        if not impacting_subsets:
            for node in color_nodes[1]:
                if color_nodes[2].intersection(ALL_NBRS[node]):
                    impacting_subsets = (color_nodes[0], color_nodes[3])
                    break
                if color_nodes[3].intersection(ALL_NBRS[node]):
                    impacting_subsets = (color_nodes[0], color_nodes[2])
                    break
        if impacting_subsets:
            other_nodes = {node for node in range(81) if value in board[node]
                           and not is_clue(node, board, solver_status)
                           and node not in components[0] and node not in components[1]}
            impacted_cells = set()
            to_remove = []
            for node in other_nodes:
                if impacting_subsets[0].intersection(ALL_NBRS[node]) \
                        and impacting_subsets[1].intersection(ALL_NBRS[node]):
                    impacted_cells.add(node)
                    to_remove.append((value, node))
            if to_remove:
                edges = [edge for edge in graph.edges
                         if edge[0] in components[0].union(components[1])]
                solver_status.capture_baseline(board, window)
                if window:
                    window.options_visible = window.options_visible.union(_get_graph_houses(edges))
                remove_options(solver_status, board, to_remove, window)
                kwargs["solver_tool"] = "multi_colors"
                kwargs["c_chain"] = {**c_chains[0], **c_chains[1]}
                kwargs["edges"] = edges
                kwargs["remove"] = to_remove
                kwargs["impacted_cells"] = impacted_cells
                # print('\nmulti colors - color trap')
                return True
        return False

    kwargs = {}
    for value in SUDOKU_VALUES_LIST:
        graph = _build_graph(value, board, solver_status)
        all_components = list(nx.connected_components(graph))
        if len(all_components) > 1:
            for ids in combinations(range(len(all_components)), 2):
                if _check_components(ids):
                    return kwargs
    return kwargs


def empty_rectangle(solver_status, board, window):
    """ The relatively good description of Empty Rectangle strategy is
     available at Sudoku Coach page (http://www.taupierbw.be/SudokuCoach/SC_EmptyRectangle.shtml)
     - although it is not complete
     Rating: 120 - 140 """

    by_row_boxes = [[[3, 6], [4, 7], [5, 8]],
                    [[0, 6], [1, 7], [2, 8]],
                    [[0, 3], [1, 4], [2, 5]]]
    by_col_boxes = [[[1, 2], [4, 5], [7, 8]],
                    [[0, 2], [3, 5], [6, 8]],
                    [[0, 1], [3, 4], [6, 7]]]

    def _find_empty_rectangle(idx, by_row):
        cells_by_x = CELLS_IN_ROW if by_row else CELLS_IN_COL
        cells_by_y = CELLS_IN_COL if by_row else CELLS_IN_ROW
        cells = cells_by_x[idx]
        opts = ''.join(board[cell] for cell in cells if not is_clue(cell, board, solver_status))
        for val in SUDOKU_VALUES_LIST:
            if opts.count(val) == 2:
                idy = [j for j in range(9) if val in board[cells[j]]]
                if CELL_SQR[idy[0]] != CELL_SQR[idy[1]]:
                    for i in range(2):
                        for j in range(2):
                            box = by_row_boxes[idx//3][idy[i]//3][j] if by_row else by_col_boxes[idx//3][idy[i]//3][j]
                            central_line = (box // 3) * 3 + 1 if by_row else (box % 3) * 3 + 1
                            box_cells = set(CELLS_IN_SQR[box])
                            central_line_cells = set(cells_by_x[central_line]).intersection(box_cells)
                            cross_cells = box_cells.intersection(central_line_cells.union(set(cells_by_y[idy[i]])))
                            rect_corners = box_cells.difference(cross_cells)
                            corners_values = ''.join(board[cell] for cell in rect_corners)
                            if corners_values.count(val) == 0:
                                hole_cells = list(central_line_cells.difference(set(cells_by_y[idy[i]])))
                                if val in board[hole_cells[0]] or val in board[hole_cells[1]]:
                                    impacted_cell = cells_by_y[idy[(i + 1) % 2]][central_line]
                                    if val in board[impacted_cell]:
                                        to_remove = [(val, impacted_cell)]
                                        if to_remove:
                                            corners = set(cell for cell in cells_by_x[idx] if val in board[cell])
                                            if val in board[hole_cells[0]]:
                                                corners.add(hole_cells[0])
                                            if val in board[hole_cells[1]]:
                                                corners.add(hole_cells[1])
                                            corners = list(corners)
                                            corners.insert(0, val)
                                            house = set(cells).union(cross_cells)
                                            solver_status.capture_baseline(board, window)
                                            solver_status.capture_baseline(board, window)
                                            if window:
                                                window.options_visible = window.options_visible.union(house)
                                            remove_options(solver_status, board, to_remove, window)
                                            kwargs["solver_tool"] = "empty_rectangle"
                                            kwargs["house"] = house
                                            kwargs["impacted_cells"] = (impacted_cell,)
                                            kwargs["remove"] = [(val, impacted_cell)]
                                            kwargs["nodes"] = corners
                                            return True
        return False

    init_options(board, solver_status)
    kwargs = {}
    for indx in range(9):
        if _find_empty_rectangle(indx, True):
            return kwargs
        if _find_empty_rectangle(indx, False):
            return kwargs
    return kwargs
