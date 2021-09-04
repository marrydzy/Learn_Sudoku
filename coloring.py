# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS

    important data structures:
    c_chain:  {node: {(candidate, color), ...}}
    colored_nodes: {candidate: {color: {cell, ...}, }, }
"""


from collections import defaultdict
from itertools import combinations

import networkx as nx

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_BOX, ALL_NBRS, SUDOKU_VALUES_LIST
from utils import get_stats, is_clue, remove_options, get_pair_house, init_options
from utils import get_strong_links, DeadEndException


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
        _add_connected(CELLS_IN_BOX[indx])
    return connected_cells


def _get_graph_houses(edges):
    """ Return complete set of houses of graph edges """
    houses = set()
    for edge in edges:
        houses = houses.union(get_pair_house(edge))
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
        _for_house(CELLS_IN_BOX[i])
    return graph


def _get_c_chain(graph, component, value, colors=('lime', 'yellow')):
    # c_chain = {node: set() for node in component}
    c_chain = defaultdict(set)
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


def _get_color_nodes(c_chain, value):
    """ Return dictionary of c_chain nodes by their color """
    color_nodes = {}
    colors = {color for node in c_chain for _, color in c_chain[node]}
    assert len(colors) == 2
    for color in colors:
        color_nodes[color] = {node for node in c_chain if (value, color) in c_chain[node]}
    return color_nodes


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
            # assert(len(edge_values) == 1)
            if len(edge_values) != 1:
                raise DeadEndException
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


@get_stats
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


@get_stats
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

    init_options(board, solver_status)
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
                        naked_xy_chain.rating += 310
                        naked_xy_chain.options_removed += len(to_remove)
                        naked_xy_chain.clues += len(solver_status.naked_singles)
                        return kwargs
    return kwargs


@get_stats
def simple_colors(solver_status, board, window):
    """ Description of the technique is available at:
    https://www.sudoku9981.com/sudoku-solving/simple-colors.php or
    https://www.sudopedia.org/wiki/Simple_Colors
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
            kwargs["solver_tool"] = "color_trap"
            kwargs["c_chain"] = c_chain
            kwargs["edges"] = edges
            kwargs["remove"] = to_remove
            kwargs["impacted_cells"] = [pair[1] for pair in to_remove]
            simple_colors.rating += 150
            simple_colors.options_removed += len(to_remove)
            simple_colors.clues += len(solver_status.naked_singles)
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
        conflicted_cells, conflicting_color = _check_houses(CELLS_IN_BOX)

        if conflicted_cells:
            assert(len(conflicting_color) == 1)
            conflicting_color = conflicting_color.pop()
            to_remove = {(value, node) for node in component if (value, conflicting_color) in c_chain[node]}
            for node in conflicted_cells:
                c_chain[node] = {(value, 'red')}
            edges = [edge for edge in graph.edges if edge[0] in component]
            solver_status.capture_baseline(board, window)
            if window:
                window.options_visible = window.options_visible.union(_get_graph_houses(edges))
            remove_options(solver_status, board, to_remove, window)
            kwargs["solver_tool"] = "color_wrap"
            kwargs["c_chain"] = c_chain
            kwargs["edges"] = edges
            kwargs["remove"] = to_remove
            simple_colors.rating += 150
            simple_colors.options_removed += len(to_remove)
            simple_colors.clues += len(solver_status.naked_singles)
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
    return None


@get_stats
def multi_colors(solver_status, board, window):
    """ Description of the technique is available at:
    https://www.sudoku9981.com/sudoku-solving/multi-colors.php or
    https://www.sudopedia.org/wiki/Multi-Colors
     Ranking of the methods is at the level of 200 ('Hard')
    """

    def _check_components(component_ids):
        components = [all_components[component_ids[0]], all_components[component_ids[1]]]
        c_chains = [_get_c_chain(graph, components[0], value, colors=('lime', 'yellow')),
                    _get_c_chain(graph, components[1], value, colors=('aqua', 'violet'))]
        if len(c_chains[0]) and len(c_chains[1]):
            if _find_color_wrap(components, c_chains, m_id=0, s_id=1):
                return True
            if _find_color_wrap(components, c_chains, m_id=1, s_id=0):
                return True
            if _find_color_wing(components, c_chains):
                return True
        return False

    def _find_color_wrap(components, c_chains, m_id, s_id):
        color_nodes = _get_color_nodes(c_chains[m_id], value)
        s_edges = {edge for edge in graph.edges if edge[0] in components[s_id]}
        for edge in s_edges:
            for color in color_nodes:
                see_color_nodes_a = color_nodes[color].intersection(ALL_NBRS[edge[0]])
                see_color_nodes_b = color_nodes[color].intersection(ALL_NBRS[edge[1]])
                if see_color_nodes_a and see_color_nodes_b:
                    edges = {edge for edge in graph.edges if edge[0] in components[m_id].union(components[s_id])}
                    to_remove = {(value, node) for node in color_nodes[color]}
                    solver_status.capture_baseline(board, window)
                    if window:
                        window.options_visible = window.options_visible.union(_get_graph_houses(edges))
                    remove_options(solver_status, board, to_remove, window)
                    c_chain = {**c_chains[m_id], **c_chains[s_id]}
                    for node in (see_color_nodes_a.pop(), see_color_nodes_b.pop()):
                        c_chain[node] = {(value, 'red')}
                    kwargs["solver_tool"] = "multi_colors-color_wrap"
                    kwargs["c_chain"] = c_chain
                    kwargs["edges"] = edges
                    kwargs["remove"] = to_remove
                    multi_colors.rating += 200
                    multi_colors.options_removed += len(to_remove)
                    multi_colors.clues += len(solver_status.naked_singles)
                    return True
        return False

    def _get_second_color(color_nodes_dir, color):
        colors = list(color_nodes_dir.keys())
        return colors[1] if color == colors[0] else colors[0]

    def _find_color_wing(components, c_chains):
        color_nodes = [_get_color_nodes(c_chains[0], value), _get_color_nodes(c_chains[1], value)]
        for color_0 in color_nodes[0]:
            for node in color_nodes[0][color_0]:
                for color_1 in color_nodes[1]:
                    if color_nodes[1][color_1].intersection(ALL_NBRS[node]):
                        other_nodes = set(range(81)).difference(components[0].union(components[1]))
                        other_nodes = {node for node in other_nodes if value in board[node]
                                       and not is_clue(node, board, solver_status)}
                        color_a = _get_second_color(color_nodes[0], color_0)
                        color_b = _get_second_color(color_nodes[1], color_1)
                        impacted_cells = set()
                        to_remove = []
                        for cell in other_nodes:
                            if color_nodes[0][color_a].intersection(ALL_NBRS[cell]) \
                                    and color_nodes[1][color_b].intersection(ALL_NBRS[cell]):
                                impacted_cells.add(cell)
                                to_remove.append((value, cell))
                        if to_remove:
                            edges = [edge for edge in graph.edges
                                     if edge[0] in components[0].union(components[1])]
                            solver_status.capture_baseline(board, window)
                            if window:
                                window.options_visible = window.options_visible.union(_get_graph_houses(edges))
                            remove_options(solver_status, board, to_remove, window)
                            kwargs["solver_tool"] = "multi_colors-color_wing"
                            kwargs["c_chain"] = {**c_chains[0], **c_chains[1]}
                            kwargs["edges"] = edges
                            kwargs["remove"] = to_remove
                            kwargs["impacted_cells"] = impacted_cells
                            multi_colors.rating += 200
                            multi_colors.options_removed += len(to_remove)
                            multi_colors.clues += len(solver_status.naked_singles)
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
    return None


@get_stats
def x_colors(solver_status, board, window):
    """ Description of the technique is available at:
     https://www.sudopedia.org/wiki/X-Colors
     The technique includes tow strategies: elimination and contradiction
     Ranking of the methods is not known
     Rating: 200 (?)
     TODO: implement a method to highlight identification of exception cells
    """
    def _find_exception_cells():
        cells = set()
        for houses in (CELLS_IN_BOX, CELLS_IN_ROW, CELLS_IN_COL):
            for house in houses:
                colored = color_nodes['lime'].union(color_nodes['yellow'])
                if not colored.intersection(house):
                    potential_cells = not_painted_cells.intersection(house)
                    potential_cells = potential_cells.difference(light_yellows if color == 'lime' else light_greens)
                    if len(potential_cells) == 1:
                        cells.add(potential_cells.pop())
        return cells

    def _get_light_colored(colored_nodes):
        light_painted = set()
        for node in colored_nodes:
            light_painted = light_painted.union({cell for cell in ALL_NBRS[node] if cell in not_painted_cells})
        return light_painted

    def _check_houses(houses, conflicted_cells):
        for house in houses:
            for key in color_nodes:
                color_cells = color_nodes[key].intersection(house)
                if len(color_cells) > 1:
                    conflicted_cells[key] = conflicted_cells[key].union(color_cells)

    def _elimination(to_be_removed):
        for cell in not_painted_cells:
            if color_nodes['lime'].intersection(ALL_NBRS[cell]) \
                    and color_nodes['yellow'].intersection(ALL_NBRS[cell]):
                to_be_removed.add((value, cell))
                impacted_cells.add(cell)
        if to_remove:   # TODO
            kwargs["solver_tool"] = "x_colors_elimination"
            # print('\ncolor_trap')
            return True
        return False

    def _contradiction(to_be_removed):
        conflicted_cells = {'lime': set(), 'yellow': set()}
        for houses in (CELLS_IN_ROW, CELLS_IN_COL, CELLS_IN_BOX):
            _check_houses(houses, conflicted_cells)
        # assert not (conflicted_cells['lime'] and conflicted_cells['yellow'])  TODO - check why it is not satisfied
        conflicted = conflicted_cells['lime'] if conflicted_cells['lime'] else conflicted_cells['yellow']
        if conflicted:
            color_true = 'yellow' if conflicted_cells['lime'] else 'lime'
            for cell in color_nodes[color_true]:
                impacted_cells.add(cell)
                for candidate in board[cell]:
                    if candidate != value:
                        to_be_removed.add((candidate, cell))
            for node in conflicted:
                c_chain[node] = {(value, 'red')}
            kwargs["solver_tool"] = "x_colors_contradiction"
            # print('\ncontradiction')
            return True
        return False

    kwargs = {}
    for value in SUDOKU_VALUES_LIST:
        graph = _build_graph(value, board, solver_status)
        for component in list(nx.connected_components(graph)):
            c_chain = _get_c_chain(graph, component, value, colors=('yellow', 'lime'))
            color_nodes = _get_color_nodes(c_chain, value)
            with_value = {cell for cell in range(81) if value in board[cell] and len(board[cell]) > 1}
            not_painted_cells = with_value.difference(color_nodes['lime'].union(color_nodes['yellow']))
            light_yellows = _get_light_colored(color_nodes['lime'])
            light_greens = _get_light_colored(color_nodes['yellow'])
            while True:
                for color in ('lime', 'yellow'):
                    exception_cells = _find_exception_cells()
                    if exception_cells:
                        for cell in exception_cells:
                            c_chain[cell] = {(value, color)}
                            color_nodes[color].add(cell)
                            not_painted_cells.remove(cell)
                            if color == 'lime':
                                light_yellows = light_yellows.union({cell for cell in ALL_NBRS[cell]
                                                                     if cell in not_painted_cells})
                            else:
                                light_greens = light_greens.union({cell for cell in ALL_NBRS[cell]
                                                                   if cell in not_painted_cells})
                        break
                else:
                    break

            to_remove = set()
            impacted_cells = set()
            if _contradiction(to_remove) or _elimination(to_remove):
                edges = {edge for edge in graph.edges if edge[0] in component}
                show_options = with_value.union(_get_graph_houses(edges))
                kwargs["c_chain"] = c_chain
                kwargs["edges"] = edges
                kwargs["impacted_cells"] = impacted_cells
                kwargs["remove"] = to_remove
                solver_status.capture_baseline(board, window)
                if window:
                    window.options_visible = window.options_visible.union(show_options)
                remove_options(solver_status, board, to_remove, window)
                x_colors.rating += 200
                x_colors.options_removed += len(to_remove)
                x_colors.clues += len(solver_status.naked_singles)
                return kwargs
    return None


@get_stats
def three_d_medusa(solver_status, board, window):
    """ Description of the technique is available at:
     https://www.sudopedia.org/wiki/3D_Medusa
     The technique includes
     - same color twice in a cell
     - same color twice in a unit (house)
     - two colors in a cell that contains uncolored candidates
     - uncolored candidate can see two opposite-colored candidates
     - uncolored candidate can see a colored one, and an oppositely colored candidate in the same cell
     Ranking of the method is at the level of 320 - 380
    """

    def _paint_bi_value_cells(links):
        for cell in bi_value_cells:
            if cell in c_chain and len(c_chain[cell]) == 1:
                candidate, color = c_chain[cell].pop()
                c_chain[cell].add((candidate, color))
                second_candidate = board[cell].replace(candidate, '')
                second_color = 'lime' if color == 'yellow' else 'yellow'
                c_chain[cell].add((second_candidate, second_color))
                if second_color in colored_nodes[second_candidate]:
                    colored_nodes[second_candidate][second_color].add(cell)
                else:
                    colored_nodes[second_candidate][second_color] = {cell}

                for other_cell in ALL_NBRS[cell]:
                    if ((cell, other_cell) in strong_links[second_candidate] or
                            (other_cell, cell) in strong_links[second_candidate]):
                        links.add((other_cell, second_candidate, color))
        return links

    def _paint_conjugate_pairs(links):
        new_links = set()
        for node, candidate, color in links:
            next_color = 'lime' if color == 'yellow' else 'yellow'
            if (candidate, color) not in c_chain[node]:
                # assert((candidate, next_color) not in c_chain[node])    TODO - check why not satisfied!
                c_chain[node].add((candidate, color))
                if color in colored_nodes[candidate]:
                    colored_nodes[candidate][color].add(node)
                else:
                    colored_nodes[candidate][color] = {node}
                for other_cell in ALL_NBRS[node]:
                    if ((node, other_cell) in strong_links[candidate] or
                            (other_cell, node) in strong_links[candidate]):
                        new_links.add((other_cell, candidate, next_color))
        return new_links

    def _check_1(to_be_removed):
        for node in c_chain:
            colors = [color for _, color in c_chain[node]]
            if colors.count('lime') > 1 or colors.count('yellow') > 1:
                false_color = 'lime' if colors.count('lime') > 1 else 'yellow'
                for cell in c_chain:
                    for candidate, color in c_chain[cell]:
                        if color == false_color:
                            to_be_removed.add((candidate, cell))
                conflicted = {candidate for candidate, color in c_chain[node] if color == false_color}
                for candidate in conflicted:
                    c_chain[node].remove((candidate, false_color))
                    c_chain[node].add((candidate, 'red'))
                return True
        return False

    def _check_2(to_be_removed):
        false_color = None
        conflicted_cells = []
        for houses in (CELLS_IN_BOX, CELLS_IN_ROW, CELLS_IN_COL):
            for house in houses:
                for candidate in colored_nodes:
                    if 'lime' in colored_nodes[candidate] and \
                            len(colored_nodes[candidate]['lime'].intersection(house)) > 1:
                        false_color = 'lime'
                        conflicted_cells = colored_nodes[candidate]['lime'].intersection(house)
                    elif 'yellow' in colored_nodes[candidate] and \
                            len(colored_nodes[candidate]['yellow'].intersection(house)) > 1:
                        false_color = 'yellow'
                        conflicted_cells = colored_nodes[candidate]['yellow'].intersection(house)
                    if false_color:
                        for cell in c_chain:
                            for option, color in c_chain[cell]:
                                if color == false_color:
                                    to_be_removed.add((option, cell))
                        for cell in conflicted_cells:
                            c_chain[cell].remove((candidate, false_color))
                            c_chain[cell].add((candidate, 'red'))
                        return True
        return False

    def _check_3(to_be_removed):
        for cell in c_chain:
            if len(board[cell]) > 2 and len({color for _, color in c_chain[cell]}) == 2:
                for candidate in board[cell]:
                    if (candidate, 'lime') not in c_chain[cell] and (candidate, 'yellow') not in c_chain[cell]:
                        to_be_removed.add((candidate, cell))
        return True if to_be_removed else False

    def _check_4(to_be_removed):
        for candidate in colored_nodes:
            if 'lime' in colored_nodes[candidate] and 'yellow' in colored_nodes[candidate]:
                cells_with_candidate = {cell for cell in range(81) if candidate in board[cell] and len(board[cell]) > 1}
                cells_with_colored = colored_nodes[candidate]['lime'].union(colored_nodes[candidate]['yellow'])
                other_cells = cells_with_candidate.difference(cells_with_colored)
                for cell in other_cells:
                    if colored_nodes[candidate]['lime'].intersection(ALL_NBRS[cell]) and \
                            colored_nodes[candidate]['yellow'].intersection(ALL_NBRS[cell]):
                        to_be_removed.add((candidate, cell))
                        impacted_cells.add(cell)
        return True if to_be_removed else False

    def _check_5(to_be_removed):
        greens = {}
        yellows = {}
        for cell in c_chain:
            if len(c_chain[cell]) == 1:
                candidate, color = c_chain[cell].pop()
                c_chain[cell].add((candidate, color))
                if color == 'lime':
                    greens[cell] = (candidate, board[cell].replace(candidate, ''))
                else:
                    yellows[cell] = (candidate, board[cell].replace(candidate, ''))
        for cell in greens:
            candidate, _ = greens[cell]
            for node in set(yellows.keys()).intersection(ALL_NBRS[cell]):
                _, other_candidates = yellows[node]
                if candidate in other_candidates:
                    to_be_removed.add((candidate, node))
                    impacted_cells.add(node)
        for cell in yellows:
            candidate, _ = yellows[cell]
            for node in set(greens.keys()).intersection(ALL_NBRS[cell]):
                _, other_candidates = greens[node]
                if candidate in other_candidates:
                    to_be_removed.add((candidate, node))
                    impacted_cells.add(node)
        return True if to_be_removed else False

    kwargs = {}
    for value in SUDOKU_VALUES_LIST:
        graph = _build_graph(value, board, solver_status)
        for component in list(nx.connected_components(graph)):
            bi_value_cells = {cell for cell in range(81) if len(board[cell]) == 2}
            strong_links = get_strong_links(board)
            c_chain = _get_c_chain(graph, component, value, colors=('yellow', 'lime'))
            edges = {edge for edge in graph.edges if edge[0] in component}
            colored_nodes = defaultdict(dict)
            colored_nodes[value] = _get_color_nodes(c_chain, value)
            additional_links = _paint_bi_value_cells(set())
            while additional_links:
                additional_links = _paint_bi_value_cells(_paint_conjugate_pairs(additional_links))
            to_remove = set()
            impacted_cells = set()
            if _check_1(to_remove) or _check_2(to_remove) or _check_3(to_remove) or _check_4(to_remove) or \
                    _check_5(to_remove):
                solver_status.capture_baseline(board, window)
                if window:
                    window.options_visible = window.options_visible.union(cell for cell in c_chain).union(
                        impacted_cells)
                remove_options(solver_status, board, to_remove, window)
                kwargs["solver_tool"] = "3d_medusa"
                kwargs["c_chain"] = c_chain
                kwargs["edges"] = edges
                kwargs["impacted_cells"] = impacted_cells
                kwargs["remove"] = to_remove
                three_d_medusa.rating += 320
                three_d_medusa.options_removed += len(to_remove)
                three_d_medusa.clues += len(solver_status.naked_singles)
                return kwargs
    return None
