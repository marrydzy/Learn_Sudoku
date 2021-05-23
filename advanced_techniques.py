# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

import networkx as nx

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import is_clue, init_options, remove_options


def _build_graph(value, solver_status, board):
    graph = nx.Graph()
    for i in range(9):
        nodes = [cell for cell in CELLS_IN_ROW[i] if value in board[cell] and not is_clue(cell, board, solver_status)]
        if len(nodes) == 2:
            graph.add_nodes_from(nodes)
            graph.add_edge(nodes[0], nodes[1])
        nodes = [cell for cell in CELLS_IN_COL[i] if value in board[cell] and not is_clue(cell, board, solver_status)]
        if len(nodes) == 2:
            graph.add_nodes_from(nodes)
            graph.add_edge(nodes[0], nodes[1])
        nodes = [cell for cell in CELLS_IN_SQR[i] if value in board[cell] and not is_clue(cell, board, solver_status)]
        if len(nodes) == 2:
            graph.add_nodes_from(nodes)
            graph.add_edge(nodes[0], nodes[1])
    return graph


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


def coloring(solver_status, board, window):
    """ TODO """

    def _check_chains(value):
        """ TODO """
        graph = _build_graph(value, solver_status, board)
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
