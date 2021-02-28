# -*- coding: UTF-8 -*-

""" CELL/OPTION selection statistics """


def collect_stats(
    data, step, board=None, next_cell=None, clue_options=None, neighbours=None
):
    """ TBD """
    if step == "init_run" and data["iter_counter"] == 0:
        cells = 0
        for cell_id in range(81):
            cells += 1 if len(board[cell_id]) == len(board[next_cell]) else 0

        opts_stat = {d: 0 for d in "123456789"}
        for cell_id in neighbours[next_cell]:
            if len(board[cell_id]) > 1:
                for value in board[cell_id]:
                    opts_stat[value] += 1
        max_freq = max(list(opts_stat.values()))
        min_freq = min(list(opts_stat.values()))

        opts_freq = []
        for clue in clue_options:
            opts_freq.append(opts_stat[clue])

        data["stat_opts"].append({})
        data["stat_opts"][-1]["opts_nb"] = len(board[next_cell])
        data["stat_opts"][-1]["opts_cells"] = cells
        data["stat_opts"][-1]["opts_iter"] = clue_options
        data["stat_opts"][-1]["opts_max_min_freq"] = max_freq - min_freq
        data["stat_opts"][-1]["opts_freq"] = opts_freq.copy()
        data["stat_opts"][-1]["opts_diff"] = max(opts_freq) - min(opts_freq)
        data["stat_opts"][-1]["opts_tot"] = sum(opts_freq)
    elif step == "run_end" and data["stat_opts"]:
        data["stat_opts"][-1]["iters"] = data["iter_counter"]
