# -*- coding: UTF-8 -*-

import pygame
import time

import graph_utils
from display import screen_messages

from html_colors import html_color_codes
from graph_utils import ANIMATION_STEP_TIME, CELL_SIZE, LEFT_MARGIN, TOP_MARGIN, CELL_COL, CELL_ROW
from graph_utils import GREY    # TODO - use html color definition!
from solver import ValueEntered, get_strategy_name


KEYBOARD_DIGITS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


class AppWindow:
    """ TODO """

    def __init__(self, board, solver_status, inspect):
        if not pygame.get_init():
            pygame.init()
        self.font_type = "FreeSans"
        self.font_clues_size = 47
        self.font_options_size = 17
        self.font_button_size = 20
        self.font_text_size = 22
        self.font_keypad_size = 40
        self.font_clues = pygame.font.SysFont(self.font_type, self.font_clues_size)
        self.font_options = pygame.font.SysFont(self.font_type, self.font_options_size, italic=True)
        self.font_text = pygame.font.SysFont(self.font_type, self.font_text_size, italic=True)
        self.font_buttons = pygame.font.SysFont(self.font_type, self.font_button_size, bold=True)
        self.font_keypad = pygame.font.SysFont(self.font_type, self.font_keypad_size, bold=False)
        self.digit_shift_x = (CELL_SIZE - self.font_clues.size('1')[0]) // 2
        self.digit_shift_y = (CELL_SIZE - self.font_clues.get_ascent()) // 2 - 2
        self.pencilmark_shift_x = (CELL_SIZE // 3 - self.font_options.size('1')[0]) // 2
        self.pencilmark_shift_y = (CELL_SIZE // 3 - self.font_options.get_ascent()) // 2
        self.pencilmark_offset = graph_utils.set_pencilmark_offset()

        self.screen = None
        self.board_cells = graph_utils.set_cell_rectangles()
        self.keypad_frame = graph_utils.set_keypad_frame()
        self.keypad_keys = graph_utils.set_keypad_keys()
        self.buttons = {}
        self.actions = {}

        self.method = graph_utils.set_methods()
        self.peep = inspect if len(inspect) else ''.join(self.method.values())
        self.inspect = self.peep

        self.solver_status = solver_status
        self.options_visible = set()
        self.selected_key = None
        self.selected_cell = None
        self.show_solution_steps = True
        self.show_wrong_values = True
        self.animate = False
        self.board_updated = False
        self.value_entered = ValueEntered(cell=None, value=None, as_clue=None)
        self.show_all_pencil_marks = False
        self.highlight_selected_digit = False
        self.critical_error = None
        self.wait = False
        self.calculate_next_clue = False
        self.suggest_technique = False

        self.time_in = 0
        self.solver_loop = None
        self.solved_board = None

        pygame.display.set_caption('SUDOKU PUZZLE')
        pygame.display.set_icon(pygame.image.load('demon.png'))  # TODO - get a better icon
        self.screen = pygame.display.set_mode(graph_utils.window_size())
        self.screen.fill(html_color_codes["gainsboro"])     # TODO - use html color definition
        graph_utils.set_buttons(self)

    def critical_error_event(self, board, **kwargs):
        """ Handle 'Critical Error' event """
        if self.buttons[pygame.K_s].is_pressed() or self.animate:
            self.show_solution_steps = True
            self.inspect = ''.join(self.method.values())
            self.animate = False
            self.show_wrong_values = True
            graph_utils.set_keyboard_status(self, False)
            graph_utils.set_btn_status(self, False)
            graph_utils.set_btn_status(self, True, (pygame.K_q, pygame.K_r))
            if "cell_solved" in kwargs:
                if len(board[kwargs["cell_solved"]]) == 1:
                    if kwargs["cell_solved"] in self.options_visible:
                        self.options_visible.remove(kwargs["cell_solved"])
                    self.solver_status.cells_solved.add(kwargs["cell_solved"])
                else:
                    self.options_visible.add(kwargs["cell_solved"])
            for cell in self.critical_error:
                if cell not in self.solver_status.givens:
                    self.options_visible.add(cell)

    def wrong_entry_event(self):
        """ Handle 'Wrong Entry' event """
        graph_utils.set_keyboard_status(self, False)
        graph_utils.set_btn_status(self, False)
        graph_utils.set_btn_status(self, True, (pygame.K_b, pygame.K_q, pygame.K_r))

    def sudoku_solved_event(self, board):
        """ Handle 'Sudoku Solved' event """
        self.animate = False
        graph_utils.set_keyboard_status(self, False)
        graph_utils.set_btn_status(self, False)
        graph_utils.set_btn_status(self, True, (pygame.K_q, pygame.K_r))

    def plain_board_event(self):
        """ Clean current board, not solved yet event  """
        graph_utils.set_btn_status(self, False, (pygame.K_b,))
        graph_utils.set_btn_status(self, True, (pygame.K_s, pygame.K_a, pygame.K_s))

    def handle_input_events(self, board, **kwargs):
        """ handle input events before entering the display loop  """
        if self.solver_loop == -1:
            self.calculate_next_clue = True
            return True

        solver_tool = kwargs.get("solver_tool")
        wrong_entry = bool("conflicted_cells" in kwargs and kwargs["conflicted_cells"] or
                           "incorrect_values" in kwargs and kwargs["incorrect_values"])

        if not solver_tool:
            pass
        elif self.critical_error:
            self.critical_error_event(board, **kwargs)
        elif wrong_entry:
            self.wrong_entry_event()
        elif kwargs["solver_tool"] == "end_of_game":
            self.sudoku_solved_event(board)
        elif not (self.show_solution_steps and self.method[kwargs["solver_tool"]] in self.inspect):
            return True
        elif solver_tool == "plain_board" or solver_tool == "plain_board_file_info":
            self.plain_board_event()
        return False

    def render_board(self, board, **kwargs):
        """ render board (TODO) """
        active_clue = kwargs.get("cell_solved")
        chain_a = kwargs.get("chain_a")
        solver_tool = kwargs.get("solver_tool", "plain_board")
        incorrect_values = kwargs.get("incorrect_values", set())
        conflicted_cells = kwargs.get("conflicted_cells", set())
        eliminated = kwargs.get("eliminate")

        black_digits = self.solver_status.givens
        if not self.critical_error:
            if active_clue:
                black_digits = black_digits.union({active_clue, })
            if chain_a:
                black_digits = black_digits.union({cell for cell in chain_a if len(board[cell]) == 1})
        red_digits = conflicted_cells.union(incorrect_values.intersection(self.solver_status.cells_solved))
        if self.critical_error:
            red_digits = red_digits.union({cell for cell in self.critical_error if cell not in black_digits})
        teal_digits = {cell for cell in self.solver_status.cells_solved if len(board[cell]) == 1}

        for row_id in range(9):
            for col_id in range(9):
                cell_id = row_id * 9 + col_id
                cell_pos = (col_id * CELL_SIZE + LEFT_MARGIN, row_id * CELL_SIZE + TOP_MARGIN)
                cell_rect = (cell_pos[0], cell_pos[1], CELL_SIZE + 1, CELL_SIZE + 1)
                pygame.draw.rect(self.screen, graph_utils.cell_color(self, cell_id, board, **kwargs), cell_rect)
                if board[cell_id] != '.':
                    if cell_id in black_digits:
                        graph_utils.render_clue(self, board[cell_id], cell_pos, html_color_codes["black"])
                    elif cell_id in red_digits:
                        graph_utils.render_clue(self, board[cell_id], cell_pos, html_color_codes["red"])
                    elif cell_id in teal_digits:
                        graph_utils.render_clue(self, board[cell_id], cell_pos, html_color_codes["teal"])
                    elif graph_utils.show_pencil_marks(self, cell_id, **kwargs):
                        if solver_tool != "plain_board":
                            graph_utils.highlight_options(self, cell_id, board[cell_id], cell_pos, **kwargs)
                        graph_utils.render_options(self, board[cell_id], cell_pos)

        if eliminated:
            for value, cell_id in eliminated:
                if self.show_all_pencil_marks or cell_id in self.options_visible:
                    cell_pos = (CELL_COL[cell_id] * CELL_SIZE + LEFT_MARGIN, CELL_ROW[cell_id] * CELL_SIZE + TOP_MARGIN)
                    graph_utils.render_options(self, value, cell_pos)

        for i in range(10):
            line_thickness = 5 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, html_color_codes["black"], (LEFT_MARGIN - 2, i * CELL_SIZE + TOP_MARGIN),
                             (LEFT_MARGIN + 9 * CELL_SIZE + 2,
                              i * CELL_SIZE + TOP_MARGIN), line_thickness)
            pygame.draw.line(self.screen, html_color_codes["black"], (i * CELL_SIZE + LEFT_MARGIN, TOP_MARGIN),
                             (i * CELL_SIZE + LEFT_MARGIN,
                              TOP_MARGIN + 9 * CELL_SIZE), line_thickness)
        graph_utils.draw_board_features(self, **kwargs)

        pygame.draw.rect(self.screen, GREY, self.keypad_frame, width=2, border_radius=9)
        for button in self.buttons.values():
            button.draw(self.screen)
        pygame.display.update()

    def draw_board(self, board, **kwargs):
        """ TODO """
        start = time.time()  # TODO - get rid of it!!!
        solver_tool = kwargs.get("solver_tool", "plain_board")

        if self.animate and solver_tool == "sashimi_x_wing":        # TODO - for DEBUG !
            self.animate = False
            self.wait = True
            self.buttons[pygame.K_a].set_pressed(False)
            graph_utils.set_btn_status(self, True, (pygame.K_b,))
            graph_utils.set_btn_status(self, False, (pygame.K_a,))
            graph_utils.set_keyboard_status(self, True)

        if self.handle_input_events(board, **kwargs):
            return True

        solver_tool_message_prefix = ''
        if self.suggest_technique:
            solver_tool_message_prefix = screen_messages["hint_on_technique"]
            kwargs = {}     # TODO: decide on options to be preserved
            self.suggest_technique = False

        self.render_board(board, **kwargs)

        incorrect_values = kwargs.get("incorrect_values", set())
        if self.critical_error:
            graph_utils.display_info(self, screen_messages["critical_error"])
        elif "conflicted_cells" in kwargs and kwargs["conflicted_cells"]:
            graph_utils.display_info(self, screen_messages["conflicting_values"])
        elif solver_tool == "end_of_game":
            graph_utils.display_info(self, screen_messages[solver_tool])
        elif self.show_wrong_values and incorrect_values:
            graph_utils.display_info(self, screen_messages["incorrect_value"])
        elif solver_tool == "options_integrity_issue":
            graph_utils.display_info(self, screen_messages["options_integrity_issue"])
        elif solver_tool != "plain_board":
            graph_utils.display_info(self, solver_tool_message_prefix + get_strategy_name(solver_tool))
        else:
            graph_utils.display_info(self, screen_messages["plain_board"])

        self.board_updated = False
        self.wait = True if solver_tool else False  # TODO - temporary only!!!

        if self.animate:
            self.board_updated = True
            self.calculate_next_clue = True
            time.sleep(ANIMATION_STEP_TIME)
        else:
            while self.wait:
                event = None
                ev = pygame.event.poll()
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    event = graph_utils.clicked_widget_id(self)
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in self.keypad_keys:
                        event = self.keypad_keys[ev.key]
                    else:
                        event = ev.key
                if event in self.actions:
                    self.actions[event](self, event, board, **kwargs)
                pygame.display.update()
        # if self.board_updated:
        #     self.input_board = board.copy()
        self.time_in += time.time() - start
        return self.board_updated

    def quit(self):
        """ TODO """
        pygame.quit()
