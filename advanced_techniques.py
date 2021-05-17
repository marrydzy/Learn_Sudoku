# -*- coding: UTF-8 -*-

""" SUDOKU SOLVING METHODS """

from itertools import combinations
import networkx as nx

from utils import CELLS_IN_ROW, CELLS_IN_COL, CELL_SQR, CELL_ROW, CELL_COL, CELLS_IN_SQR
from utils import ALL_NBRS, SUDOKU_VALUES_LIST
from utils import is_clue, init_options, remove_options


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


def coloring(solver_status, board, window):

    def _find_chain(value):
        graph = nx.Graph()
        for row in range(9):
            nodes = list(
                cell for cell in CELLS_IN_ROW[row] if value in board[cell] and not is_clue(cell, board, solver_status))
            if len(nodes) == 2:
                graph.add_nodes_from(nodes)
                graph.add_edge(nodes[0], nodes[1])
        for col in range(9):
            nodes = list(
                cell for cell in CELLS_IN_COL[col] if value in board[cell] and not is_clue(cell, board, solver_status))
            if len(nodes) == 2:
                graph.add_nodes_from(nodes)
                graph.add_edge(nodes[0], nodes[1])
        for box in range(9):
            nodes = list(
                cell for cell in CELLS_IN_SQR[box] if value in board[cell] and not is_clue(cell, board, solver_status))
            if len(nodes) == 2:
                graph.add_nodes_from(nodes)
                graph.add_edge(nodes[0], nodes[1])


        DEBUG = True

        if DEBUG:
            print()
            print(f'{value = }')
            print(f'{list(graph.nodes) = }')
            print(f'{[(node, graph.degree[node]) for node in graph.nodes]}')
            print(f'{nx.algorithms.components.number_connected_components(graph) = }')
            print(f'{list(nx.connected_components(graph)) = }')
            print(f'{list(nx.algorithms.chains.chain_decomposition(graph)) = }')
        chains = list(nx.algorithms.chains.chain_decomposition(graph))
        if chains:
            fins = [node for node in graph.nodes if graph.degree[node] == 1]
            for chain in chains:
                if chain[0][0] == chain[-1][1]:
                    nodes = [edge[1] for edge in chain]
                    for fin in fins:
                        for node in nodes:
                            if (fin, node) in graph.edges:
                                corners = []
                                assert(graph.degree[node] == 3)
                                corners.append(fin)
                                corners.extend(nodes[nodes.index(node):])
                                corners.extend(nodes[:nodes.index(node)])
                                if DEBUG:
                                    print(f'{nodes = }')
                                    print(f'{corners = }')
                                other_cells = [cell for cell in range(81) if cell not in corners
                                               and value in board[cell]
                                               and not is_clue(cell, board, solver_status)]
                                to_remove = []
                                impacted_cells = set()
                                for cell in other_cells:
                                    impacting_nodes = set(corners).intersection(set(ALL_NBRS[cell]))
                                    if len(impacting_nodes) > 1:
                                        for pair in combinations(impacting_nodes, 2):
                                            indx_1 = corners.index(pair[0])
                                            indx_2 = corners.index(pair[1])
                                            if indx_1 % 2 != indx_2 % 2:
                                                impacted_cells.add(cell)
                                                to_remove.append((value, cell))
                                if to_remove:
                                    solver_status.capture_baseline(board, window)
                                    if window:
                                        window.options_visible = window.options_visible.union(set(corners).union(impacted_cells))
                                    remove_options(solver_status, board, to_remove, window)
                                    corners.insert(0, value)
                                    kwargs["solver_tool"] = "coloring"
                                    kwargs["nodes"] = corners
                                    kwargs["snake"] = corners[1:]
                                    kwargs["remove"] = to_remove
                                    kwargs["impacted_cells"] = impacted_cells
                                    return True
        return False

    kwargs = {}
    for opt in SUDOKU_VALUES_LIST:
        if _find_chain(opt):
            return kwargs
    return kwargs
