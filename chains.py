# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from collections import defaultdict

import networkx as nx

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import is_clue, init_options, remove_options


def _assign_chain_nodes_colors(graph, chain_nodes):
    color = 'g'
    for node in chain_nodes:
        graph.nodes[node]['color'] = color
        color = 'y' if color == 'g' else 'g'


def _assign_fin_nodes_colors(graph, fin):
    pos = -1
    cntr = 1
    color = graph.nodes[fin[pos]]['color']
    while cntr < len(fin):
        color = 'y' if color == 'g' else 'g'
        pos -= 1
        graph.nodes[fin[pos]]['color'] = color
        cntr += 1


def _get_fin(graph, chain_nodes, fin_end):
    junctions = [node for node in chain_nodes if graph.degree[node] == 3]
    the_fin = []
    fin_len = None
    for node_t in junctions:
        fin = nx.algorithms.shortest_paths.generic.shortest_path(graph, fin_end, node_t)
        if fin_len is None or len(fin) < fin_len:
            fin_len = len(fin)
            the_fin = fin
    _assign_fin_nodes_colors(graph, the_fin)
    return the_fin


def _get_u_loop(graph, chain_nodes, other_chain):
    u_loop = []
    if len(other_chain) > 1 and other_chain[0][0] != other_chain[-1][1] \
            and other_chain[0][0] in chain_nodes and other_chain[-1][1] in chain_nodes:
        color = graph.nodes[other_chain[0][0]]['color']
        for edge in other_chain:
            u_loop.append(edge[0])
            graph.nodes[u_loop[-1]]['color'] = color
            color = 'y' if color == 'g' else 'g'
        u_loop.append(other_chain[-1][1])
        assert(graph.nodes[u_loop[-1]]['color'] == color)
    return u_loop


def _get_strongly_connected_cells(board, solver_status):
    """ returns dictionary of strongly connected cells
    connected_cells data format:
    {(cell_1, cell_2): [candidate_1, candidate_2, ...], ...} """

    def _add_connected(cells):
        unsolved_cells = [cell for cell in cells if not is_clue(cell, board, solver_status)]
        if unsolved_cells:
            candidates = ''.join(board[cell] for cell in unsolved_cells)
            for value in SUDOKU_VALUES_LIST:
                if candidates.count(value) == 2:
                    cells_pair = tuple([cell for cell in unsolved_cells if value in board[cell]])
                    assert(len(cells_pair) == 2)
                    connected_cells[cells_pair].append(value)
                    # if value == '8':
                        # print(f'{cells_pair = }')

    connected_cells = defaultdict(list)
    for indx in range(9):
        _add_connected(CELLS_IN_ROW[indx])
        _add_connected(CELLS_IN_COL[indx])
        _add_connected(CELLS_IN_SQR[indx])
    return connected_cells


def _check_bidirectional_traversing(end_value, path, board):
    def _traverse(nodes):
        exp_value = end_value
        for node in nodes:
            exp_value = board[node].replace(exp_value, '')
            if len(exp_value) != 1:
                return False
        # print(f'{exp_value = }')
        return True if exp_value == end_value else False

    if len(path) < 3:
        return False
    return _traverse(path) and _traverse(path[-1::-1])


paths = []
max_path = 100


def _walk(board, graph, path, start_node, start_value, end_node, end_value):
    """ walks possible paths between start_node and end_node,
    starting with start value
    Returns:
        True if the only value in end_node can be end_value,
        False otherwise
    """
    global paths
    global max_path

    if len(path) > max_path:
        return False

    path.append(start_node)
    # print(f'{start_node = }\t{start_value = }  {path = }')
    current_node = start_node
    current_value = start_value
    assert(start_value in board[start_node])
    if current_node == end_node:
        print(f'ended with {start_value}')
        if current_value == end_value:
            paths.append(path.copy())
            max_path = len(path)
    else:
        for next_node, attr in graph.adj[current_node].items():
            # print(f'{next_node = }  {attr = }')
            if next_node not in path:
                edge_values = set(attr['candidates'])
                for value in edge_values:
                    if value != current_value and value in board[next_node]:
                        _walk(board, graph, path.copy(), next_node, value, end_node, end_value)


def hidden_xy_chain(solver_status, board, window):
    """ TODO """

    global paths

    # TODO - temporary for development/testing only!
    if True:
        board[18] = '68'
        board[19] = '356'
        board[30] = '46'
        board[31] = '256'
        board[32] = '24'
        board[33] = '59'
        board[35] = '13'
        board[36] = '89'
        board[44] = '79'
        board[50] = '78'
        board[51] = '13'
        board[62] = '37'
        board[80] = '48'

    def _dbg_print_adj(node):
        print(f'\n{node = }  {board[node] = }')
        for n, attr in graph.adj[node].items():
            print(f'{n = } \t{attr["candidates"] = }')

    connected_cells = _get_strongly_connected_cells(board, solver_status)
    graph = nx.Graph()
    for edge, candidates in connected_cells.items():
        graph.add_edge(*edge, candidates=candidates)

    """
    print(f'\n{dict(graph[66]) = }')
    print(f'\n{dict(graph[48]) = }')
    print(f'\n{dict(graph[52]) = }')
    print(f'\n{dict(graph[44]) = }')
    print(f'\n{dict(graph[26]) = }')
    print(f'\n{dict(graph[6]) = }')
    """

    unresolved = [cell for cell in range(81) if len(board[cell]) > 2]
    kwargs = {}

    for cell in [69,]: # unresolved:
        for candidate in ['8']: # board[cell]:
            for component in nx.connected_components(graph):
                ends = set()
                nodes = component.intersection(set(ALL_NBRS[cell]))
                for node_1, node_2, candidates in graph.edges.data('candidates'):
                    if candidate in candidates:
                        # assert(node_1 not in nodes or node_2 not in nodes)
                        if node_1 in nodes:
                            ends.add(node_1)
                        if node_2 in nodes:
                            ends.add(node_2)
                print(f'\n{ends = }')
                if len(ends) == 2:
                    path = []
                    # path = nx.algorithms.shortest_paths.generic.shortest_path(graph, ends.pop(), ends.pop())
                    # print(f'{path = }')
                    # _dbg_print_adj(66)
                    # _dbg_print_adj(48)
                    # _dbg_print_adj(12)
                    visited_nodes = []
                    _walk(board, graph, visited_nodes, 66, '7', 6, '8')
                    print()
                    print(paths)
                    print()
                    print(f'{len(paths) = }')
                    min_length = 100
                    for p in paths:
                        min_length = len(p) if len(p) < min_length else min_length
                        print(f'{len(p) = }')
                    print()
                    for p in paths:
                        if len(p) == min_length:
                            print(p)
                            path = p
                            break
                    if path:
                        to_remove = [(candidate, cell), ]
                        path.insert(0, candidate)
                        solver_status.capture_baseline(board, window)
                        if window:
                            window.options_visible = window.options_visible.union(set(path)).union({cell})
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "hidden_xy_chain"
                        kwargs["impacted_cells"] = [cell, ]
                        kwargs["remove"] = to_remove
                        kwargs["finned_x_wing"] = path  # TODO!!!
                        return kwargs

    # board[69] = '136'   # TODO - for testing purposes only!
    return kwargs


def naked_xy_chain(solver_status, board, window):
    """ A decent description of the technique is available
    at: http://www.sudokusnake.com/nakedxychains.php
    The strategy is assessed as 'Hard', 'Unfair', or 'Diabolical'.
    Ranking of the method (called XY-Chain) varies widely
    260 and 900
    Comments:
    Building a graph and identifying potential chains (paths) was straightforward.
    A slightly tricky part was to check for possibility of bidirectional traversing
    between end nodes of the potential paths """

    def _build_graph():
        bi_value_cells = set(cell for cell in range(81) if len(board[cell]) == 2)
        graph = nx.Graph()
        graph.add_nodes_from(bi_value_cells)
        for cell in bi_value_cells:
            neighbours = set(ALL_NBRS[cell]).intersection(bi_value_cells)
            graph.add_edges_from([(cell, other_cell) for other_cell in neighbours
                                  if len(set(board[cell]).intersection(set(board[other_cell]))) == 1])
        return graph

    graph = _build_graph()
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
                    assert(len(ends) == 2)
                    path = nx.algorithms.shortest_paths.generic.shortest_path(graph, ends[0], ends[1])
                    if _check_bidirectional_traversing(candidate, path, board):
                        to_remove = [(candidate, cell), ]
                        path.insert(0, candidate)
                        solver_status.capture_baseline(board, window)
                        if window:
                            window.options_visible = window.options_visible.union(set(path)).union({cell})
                        remove_options(solver_status, board, to_remove, window)
                        kwargs["solver_tool"] = "naked_xy_chain"
                        kwargs["impacted_cells"] = [cell, ]
                        kwargs["remove"] = to_remove
                        kwargs["finned_x_wing"] = path     # TODO!!!
                        return kwargs

    return kwargs



def coloring(solver_status, board, window):
    """ TODO """

    def _build_graph(value):
        graph = nx.Graph()
        for i in range(9):
            nodes = [cell for cell in CELLS_IN_ROW[i] if
                     value in board[cell] and not is_clue(cell, board, solver_status)]
            if len(nodes) == 2:
                graph.add_nodes_from(nodes)
                graph.add_edge(nodes[0], nodes[1])
            nodes = [cell for cell in CELLS_IN_COL[i] if
                     value in board[cell] and not is_clue(cell, board, solver_status)]
            if len(nodes) == 2:
                graph.add_nodes_from(nodes)
                graph.add_edge(nodes[0], nodes[1])
            nodes = [cell for cell in CELLS_IN_SQR[i] if
                     value in board[cell] and not is_clue(cell, board, solver_status)]
            if len(nodes) == 2:
                graph.add_nodes_from(nodes)
                graph.add_edge(nodes[0], nodes[1])
        return graph

    def _check_chains(value):
        """ TODO """
        graph = _build_graph(value)
        for component in list(nx.connected_components(graph)):
            ends = list(node for node in component if graph.degree[node] == 1)
            if ends:
                chains = list(nx.algorithms.chains.chain_decomposition(graph, ends[0]))
                if chains:
                    chain = chains[0]
                    if chain[0][0] == chain[-1][1]:
                        chain_nodes = [edge[0] for edge in chain]
                        _assign_chain_nodes_colors(graph, chain_nodes)
                        appendixes = [_get_fin(graph, chain_nodes, end) for end in ends]
                        appendixes.extend([_get_u_loop(graph, chain_nodes, other_chain) for other_chain in chains[1:]])
                        if _check_if_conflict(graph, chain_nodes, appendixes, value):
                            return True
                        if _check_if_pointing(graph, chain_nodes, appendixes, value):
                            return True
        return False

    def _check_if_pointing(graph, chain_nodes, appendixes, value):
        spider_web = set(chain_nodes)
        for fin in appendixes:
            spider_web = spider_web.union(set(fin))

        impacted_cells = [cell for cell in range(81) if cell not in spider_web and value in board[cell]
                          and not is_clue(cell, board, solver_status)]
        for cell in impacted_cells:
            impacting_web_nodes = spider_web.intersection(set(ALL_NBRS[cell]))
            web_nodes_colors = set(graph.nodes[node]['color'] for node in impacting_web_nodes)
            if len(web_nodes_colors) > 1:
                chain_nodes.append(chain_nodes[0])
                to_remove = [(value, cell), ]
                solver_status.capture_baseline(board, window)
                if window:
                    window.options_visible = window.options_visible.union(spider_web)
                remove_options(solver_status, board, to_remove, window)
                corners = list(spider_web)
                corners = [(node, graph.nodes[node]['color']) for node in corners]
                corners.insert(0, value)
                kwargs["solver_tool"] = "coloring"
                kwargs["colored_chain"] = corners
                kwargs["remove"] = to_remove
                kwargs["impacted_cells"] = [cell, ]
                kwargs["appendixes"] = appendixes
                kwargs["snake"] = chain_nodes
                return True
        return False

    def _check_if_conflict(graph, chain_nodes, appendixes, value):
        spider_web = set(chain_nodes)
        for fin in appendixes:
            spider_web = spider_web.union(set(fin))

        impacted_cells = None
        for i in range(9):
            house_nodes = list(spider_web.intersection(set(CELLS_IN_ROW[i])))
            if len(house_nodes) > 1:
                assert(len(house_nodes) == 2)
                colors = set(graph.nodes[node]['color'] for node in house_nodes)
                if len(colors) == 1:
                    impacted_cells = house_nodes
                    break
            house_nodes = list(spider_web.intersection(set(CELLS_IN_COL[i])))
            if len(house_nodes) > 1:
                assert (len(house_nodes) == 2)
                colors = set(graph.nodes[node]['color'] for node in house_nodes)
                if len(colors) == 1:
                    impacted_cells = house_nodes
                    break
            house_nodes = list(spider_web.intersection(set(CELLS_IN_COL[i])))
            if len(house_nodes) > 1:
                assert (len(house_nodes) == 2)
                colors = set(graph.nodes[node]['color'] for node in house_nodes)
                if len(colors) == 1:
                    impacted_cells = house_nodes
                    break

        if impacted_cells:
            chain_nodes.append(chain_nodes[0])
            to_remove = [(value, node) for node in impacted_cells]
            solver_status.capture_baseline(board, window)
            if window:
                window.options_visible = window.options_visible.union(spider_web)
            remove_options(solver_status, board, to_remove, window)
            corners = list(spider_web.difference(set(impacted_cells)))
            corners = [(node, graph.nodes[node]['color']) for node in corners]
            corners.insert(0, value)
            kwargs["solver_tool"] = "coloring"
            kwargs["colored_chain"] = corners
            kwargs["remove"] = to_remove
            kwargs["impacted_cells"] = impacted_cells
            kwargs["appendixes"] = appendixes
            kwargs["snake"] = chain_nodes
            return True
        return False

    kwargs = {}
    for val in SUDOKU_VALUES_LIST:
        if _check_chains(val):
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
