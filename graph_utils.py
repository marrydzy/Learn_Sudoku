import time
import sys
import pygame

from collections import defaultdict

import utils
from solver import solver_status, ValueEntered

from utils import set_remaining_candidates, get_cell_candidates
from utils import CELL_ROW, CELL_COL
from html_colors import html_color_codes


ANIMATION_STEP_TIME = 0.1
BUTTON_PRESS_TIME = 0.15

CELL_ID_OFFSET = 1000

# dimensions of sudoku board:
CELL_SIZE = 66
LEFT_MARGIN = 25
TOP_MARGIN = 60
BOTTOM_MARGIN = 90


# TODO: Obsolete - to be removed!!!
DARKGREY = (120, 120, 120)
GREY = (160, 160, 160)
LIGHTPINK = (255, 182, 193)
LIGHTGREY = (200, 200, 200)


C_PRESSED_BTN_BORDER = (31, 62, 50)
C_PRESSED_BTN_FACE = (77, 110, 96)      # (68, 110, 100)
C_OTHER_CELLS = (255, 250, 190)
Y_WING_ROOT = (255, 153, 51)
Y_WING_LEAF = (255, 153, 51)


# dimensions of control buttons:
BUTTON_H = 45
BUTTONS_OFFSET = 10

KEYPAD_DIGIT_W = 65
KEYPAD_DIGIT_H = 65
KEYPAD_DIGIT_OFFSET = 10
KEYPAD_LEFT_MARGIN = 75
KEYPAD_TOP_MARGIN = 75
KEYPAD_TO_KEYS = 15


class Button:
    """ TODO """
    def __init__(self, btn_id, rect, text, font,
                 border_color=html_color_codes["darkseagreen"],
                 face_color=html_color_codes["lightgray"],
                 font_color=(50, 50, 50),   # TODO
                 disable_border_color=LIGHTGREY,
                 disable_face_color=html_color_codes["white"],
                 disable_font_color=html_color_codes["gainsboro"], pressed_border_color=C_PRESSED_BTN_BORDER,
                 pressed_face_color=C_PRESSED_BTN_BORDER,
                 pressed_font_color=html_color_codes["white"]):
        self.btn_id = btn_id
        self.rect = rect
        self.text = text
        self.border_color = border_color
        self.face_color = face_color
        self.font_color = font_color
        self.disable_border_color = disable_border_color
        self.disable_face_color = disable_face_color
        self.disable_font_color = disable_font_color
        self.pressed_border_color = pressed_border_color
        self.pressed_face_color = pressed_face_color
        self.pressed_font_color = pressed_font_color
        self.font = font
        self.txt_x = rect[0] + (rect[2] - self.font.size(self.text)[0]) // 2
        self.txt_y = rect[1] + (rect[3] - self.font.get_ascent()) // 2
        self.active = True
        self.pressed = False

    def draw(self, screen):
        """ TODO """
        if self.active and not self.pressed:
            pygame.draw.rect(screen, self.face_color, self.rect, border_radius=9)
            pygame.draw.rect(screen, self.border_color, self.rect, width=2, border_radius=9)
            btn_txt = self.font.render(self.text, True, self.font_color)
            screen.blit(btn_txt, (self.txt_x, self.txt_y))
        elif not self.active:
            pygame.draw.rect(screen, self.face_color, self.rect, border_radius=9)
            pygame.draw.rect(screen, self.disable_border_color, self.rect, width=2, border_radius=9)
            btn_txt = self.font.render(self.text, True, self.disable_font_color)
            screen.blit(btn_txt, (self.txt_x, self.txt_y))
        elif self.pressed:
            pygame.draw.rect(screen, self.pressed_face_color, self.rect, border_radius=9)
            pygame.draw.rect(screen, self.pressed_border_color, self.rect, width=2, border_radius=9)
            btn_txt = self.font.render(self.text, True, self.pressed_font_color)
            screen.blit(btn_txt, (self.txt_x, self.txt_y))

    def press_and_release(self, screen, deactivate=True):
        if self.active and not self.pressed:
            self.pressed = True
            self.draw(screen)
            pygame.display.update()
            time.sleep(BUTTON_PRESS_TIME)
            self.pressed = False
            self.active = False if deactivate else True
            self.draw(screen)
            pygame.display.update()

    def being_pressed(self, wait_to_release=False):
        """ TODO """
        if self.active and not wait_to_release and self.rect.collidepoint(pygame.mouse.get_pos()):
            return True
        return False

    def set_status(self, enable):
        self.active = enable

    def is_active(self):
        return self.active

    def set_pressed(self, pressed):
        self.pressed = pressed

    def is_pressed(self):
        return self.pressed


def show_pencil_marks(window, cell, **kwargs):
    """ Check if to show pencil marks for a given cell
    If the cell options are presented to show working of a solver method,
    the cell id will be added to the set of cells where options are displayed """

    if window.show_all_pencil_marks:
        return True
    if cell not in window.options_visible:
        if "impacted_cells" in kwargs and cell in kwargs["impacted_cells"]:
            window.options_visible.add(cell)
        if "claims" in kwargs and cell in kwargs["house"]:
            window.options_visible.add(cell)
        if "y_wing" in kwargs and kwargs["y_wing"] and cell in kwargs["y_wing"][1:]:
            window.options_visible.add(cell)
    return True if cell in window.options_visible else False


def render_clue(window, clue, pos, color):
    """ Render board clue """
    digit = window.font_clues.render(clue, True, color)
    window.screen.blit(digit, (pos[0] + window.digit_shift_x, pos[1] + window.digit_shift_y))


def render_options(window, options, pos):
    """ Render cell options (pencil marks) """
    for value in options:
        digit = window.font_options.render(value, True, html_color_codes['black'])
        window.screen.blit(digit, (pos[0] + window.pencilmark_offset[value][0] + window.pencilmark_shift_x,
                           pos[1] + window.pencilmark_offset[value][1] + window.pencilmark_shift_y))


def cell_color(window, cell, board, **kwargs):
    """ TODO """
    color = html_color_codes["white"]
    if window.highlight_selected_digit and utils.is_digit(cell, board, window.solver_status) and \
            board[cell] == window.selected_key:
        color = html_color_codes["moccasin"]
    if "house" in kwargs and kwargs["house"] and cell in kwargs["house"]:
        color = html_color_codes["lightyellow"]
    if "greyed_out" in kwargs and cell in kwargs["greyed_out"]:
        color = html_color_codes["silver"]
    if "c_chain" in kwargs and cell in kwargs["c_chain"]:
        color = html_color_codes["orange"]
    if "chain_a" in kwargs and cell in kwargs["chain_a"]:
        # color = html_color_codes["orange"]
        # color = html_color_codes["moccasin"]
        # color = html_color_codes["sandybrown"]
        color = html_color_codes["lightsalmon"]

    if "chain_b" in kwargs and cell in kwargs["chain_b"]:
        color = html_color_codes["peru"]
    if "chain_c" in kwargs and cell in kwargs["chain_c"]:
        color = html_color_codes["lightcoral"]
    if "chain_d" in kwargs and cell in kwargs["chain_d"]:
        color = html_color_codes["yellow"]
    if "chain_i" in kwargs and cell in kwargs["chain_i"]:
        color = html_color_codes["lightyellow"]
    if "impacted_cells" in kwargs and cell in kwargs["impacted_cells"]:
        # color = html_color_codes["palegreen"]
        # color = html_color_codes["moccasin"]
        color = html_color_codes["lightgreen"]

    if cell == window.selected_cell or \
            "cell_solved" in kwargs and cell == kwargs["cell_solved"]:
        color = html_color_codes["palegreen"]
    if "conflicted_cells" in kwargs and cell in kwargs["conflicted_cells"]:
        color = html_color_codes["pink"]
    if "incorrect_values" in kwargs and cell in kwargs["incorrect_values"]:
        color = html_color_codes["pink"]
    if window.critical_error and cell in window.critical_error:
        color = html_color_codes["pink"]
    return color


def display_info(window, text):
    """ Display info 'text' starting at the left top corner of the window """
    if text:
        msg = window.font_text.render(text, True, html_color_codes['black'])
        top_margin = (TOP_MARGIN - window.font_text.get_ascent()) // 2
        info_rect = pygame.Rect((LEFT_MARGIN, top_margin, window_size()[0] - 2 * LEFT_MARGIN, window.font_text_size+1))
        pygame.draw.rect(window.screen, html_color_codes["gainsboro"], info_rect)
        window.screen.set_clip(info_rect)
        window.screen.blit(msg, (LEFT_MARGIN, top_margin))
        window.screen.set_clip(None)
        pygame.display.update()


def draw_keypad(window):
    """ TODO """
    pygame.draw.rect(window.screen, DARKGREY, window.keypad_frame, width=1, border_radius=9)


def draw_board_features(window, **kwargs):
    """ TBD """

    rectangle = kwargs.get("rectangle")
    wxy_wing = kwargs.get("wxy_wing")
    skyscraper = kwargs.get("skyscraper")
    edges = kwargs.get("edges")

    if rectangle:
        left = (rectangle[0] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        top = (rectangle[0] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        right = (rectangle[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        bottom = (rectangle[2] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        rect = pygame.Rect(left, top, right - left, bottom - top)
        pygame.draw.rect(window.screen, html_color_codes["magenta"], rect, width=4)

    if skyscraper:
        color = html_color_codes["magenta"]
        skyscraper = skyscraper[1:]
        x1 = (skyscraper[0] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y1 = (skyscraper[0] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        x2 = (skyscraper[2] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y2 = (skyscraper[2] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        pygame.draw.line(window.screen, color, (x1, y1), (x2, y2), width=5)
        x1 = (skyscraper[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y1 = (skyscraper[1] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        x2 = (skyscraper[3] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y2 = (skyscraper[3] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        pygame.draw.line(window.screen, color, (x1, y1), (x2, y2), width=5)

    y_wing = wxy_wing
    if y_wing:
        x1 = (y_wing[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y1 = (y_wing[1] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        root = (x1, y1)
        for leaf in y_wing[2:]:
            x2 = (leaf % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            y2 = (leaf // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
            width = 4 if x1 == x2 or y1 == y2 else 5
            pygame.draw.line(window.screen, html_color_codes["magenta"], root, (x2, y2), width=width)

    if edges:
        color = html_color_codes["magenta"]
        two_way_segments_by_row, two_way_segments_by_col = get_two_way_segments(edges)
        for edge in edges:
            if is_overlapping(edge, two_way_segments_by_row, two_way_segments_by_col):
                _draw_two_way_edge(window, edge, color)
            else:
                x1 = (edge[0] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
                y1 = (edge[0] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
                x2 = (edge[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
                y2 = (edge[1] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
                pygame.draw.line(window.screen, color, (x1, y1), (x2, y2),
                                 width=5 if abs(x2 - x1) == abs(y2 - y1) else 4)
    """
    if chains:
        color = html_color_codes["magenta"]
        for appendix in chains:
            for node in range(len(appendix) - 1):
                x1 = (appendix[node] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
                y1 = (appendix[node] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
                x2 = (appendix[node + 1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
                y2 = (appendix[node + 1] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
                pygame.draw.line(window.screen, color, (x1, y1), (x2, y2),
                                 width=5 if abs(x2 - x1) == abs(y2 - y1) else 4)
    """


def _draw_two_way_edge(window, edge, color):
    """ Draw an edge that overlaps two-way segment """
    offset = 0.15 * CELL_SIZE
    right_down = True
    horizontal = True
    if edge[0] < edge[1]:
        node_a, node_b = edge[0], edge[1]
    else:
        right_down = False
        node_a, node_b = edge[1], edge[0]
    x1 = (node_a % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
    y1 = (node_a // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
    x2 = (node_b % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
    y2 = (node_b // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
    if x1 == x2:
        horizontal = False
    segments = [(x1, y1)]
    if horizontal:
        if right_down:
            segments.append((x1+offset, y1+offset))
            segments.append((x2-offset, y2+offset))
            segments.append((x2, y2))
        else:
            segments.append((x1+offset, y1-offset))
            segments.append((x2-offset, y2-offset))
            segments.append((x2, y2))
    else:
        if right_down:
            segments.append((x1+offset, y1+offset))
            segments.append((x2+offset, y2-offset))
            segments.append((x2, y2))
        else:
            segments.append((x1-offset, y1+offset))
            segments.append((x2-offset, y2-offset))
            segments.append((x2, y2))
    for i in range(3):
        pygame.draw.line(window.screen, color, segments[i], segments[i+1], width=4 if i == 1 else 5)


def get_two_way_segments(edges):
    """ Get nodes that belong to two or more edges """
    by_row = defaultdict(list)
    by_col = defaultdict(list)
    for edge in edges:
        cell_id = edge[0] if edge[0] < edge[1] else edge[1]
        cell_stop = edge[1] if edge[0] < edge[1] else edge[0]
        if CELL_ROW[edge[0]] == CELL_ROW[edge[1]]:
            while cell_id < cell_stop:
                by_row[CELL_ROW[edge[0]]].append(cell_id)
                cell_id += 1
        elif CELL_COL[edge[0]] == CELL_COL[edge[1]]:
            while cell_id < cell_stop:
                by_col[CELL_COL[edge[0]]].append(cell_id)
                cell_id += 9
    in_rows = defaultdict(set)
    for row in by_row:
        for cell in by_row[row]:
            if by_row[row].count(cell) > 1:
                in_rows[row].add(cell)
    in_cols = defaultdict(set)
    for col in by_col:
        for cell in by_col[col]:
            if by_col[col].count(cell) > 1:
                in_cols[col].add(cell)
    return in_rows, in_cols


def is_overlapping(edge, two_way_segments_by_row, two_way_segments_by_col):
    """ Check if the edge includes two_way_segment """
    cell_id = edge[0] if edge[0] < edge[1] else edge[1]
    cell_stop = edge[1] if edge[0] < edge[1] else edge[0]
    if CELL_ROW[edge[0]] == CELL_ROW[edge[1]]:
        if CELL_ROW[edge[0]] in two_way_segments_by_row:
            while cell_id <= cell_stop:
                if cell_id in two_way_segments_by_row[CELL_ROW[edge[0]]]:
                    return True
                cell_id += 1
    elif CELL_COL[edge[0]] == CELL_COL[edge[1]]:
        if CELL_COL[edge[0]] in two_way_segments_by_col:
            while cell_id <= cell_stop:
                if cell_id in two_way_segments_by_col[CELL_COL[edge[0]]]:
                    return True
                cell_id += 9
    return False


def highlight_options(window, cell_id, new_value, pos, **kwargs):
    """ Highlight pencil marks, as applicable """

    global chain_counter

    eliminate = kwargs.get("eliminate")
    claims = kwargs.get("claims")
    iterate = kwargs.get("iterate")
    xy_wing = kwargs.get("y_wing")
    wxy_wing = kwargs.get("wxy_wing")
    skyscraper = kwargs.get("skyscraper")
    sue_de_coq = kwargs.get("sue_de_coq")
    nodes = kwargs.get("nodes")
    c_chain = kwargs.get("c_chain")
    chain_a = kwargs.get("chain_a")
    chain_b = kwargs.get("chain_b")
    chain_c = kwargs.get("chain_c")
    chain_d = kwargs.get("chain_d")
    chain_i = kwargs.get("chain_i")

    if iterate is not None and cell_id == iterate:
        pygame.draw.rect(
            window.screen, LIGHTPINK,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if xy_wing is not None and cell_id == xy_wing[1] or wxy_wing is not None and cell_id == wxy_wing[1]:
        pygame.draw.rect(
            window.screen, Y_WING_ROOT,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if xy_wing is not None and (cell_id == xy_wing[2] or cell_id == xy_wing[3]):
        pygame.draw.rect(
            window.screen, Y_WING_LEAF,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if wxy_wing is not None and (cell_id == wxy_wing[2] or cell_id == wxy_wing[3] or cell_id == wxy_wing[4]):
        pygame.draw.rect(
            window.screen, Y_WING_LEAF,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if nodes and cell_id in nodes[1:]:
        pygame.draw.rect(
            window.screen, Y_WING_LEAF,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if skyscraper and cell_id in skyscraper[1:]:
        pygame.draw.rect(
            window.screen, Y_WING_LEAF,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if sue_de_coq and cell_id in sue_de_coq:
        pygame.draw.rect(
            window.screen, Y_WING_LEAF,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))

    if chain_i:
        if cell_id in chain_i:
            for value, color in chain_i[cell_id]:
                pygame.draw.rect(window.screen, html_color_codes[color],
                                 (pos[0] + window.pencilmark_offset[value][0],
                                  pos[1] + window.pencilmark_offset[value][1],
                                  CELL_SIZE // 3, CELL_SIZE // 3))

    for value in window.solver_status.board_baseline[cell_id]:
        if claims and value in new_value and cell_id in claims:
            pygame.draw.rect(window.screen, html_color_codes["cyan"],
                             (pos[0] + window.pencilmark_offset[value][0],
                              pos[1] + window.pencilmark_offset[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if claims and (value, cell_id) in claims:
            pygame.draw.rect(window.screen, html_color_codes["cyan"],
                             (pos[0] + window.pencilmark_offset[value][0],
                              pos[1] + window.pencilmark_offset[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if xy_wing and value == xy_wing[0] and cell_id in xy_wing[1:] or \
                wxy_wing and value == wxy_wing[0] and cell_id in wxy_wing[1:]:
            pygame.draw.rect(window.screen, html_color_codes["cyan"],
                             (pos[0] + window.pencilmark_offset[value][0],
                              pos[1] + window.pencilmark_offset[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if nodes and value == nodes[0] and cell_id in nodes[1:]:
            pygame.draw.rect(window.screen, html_color_codes["cyan"],
                             (pos[0] + window.pencilmark_offset[value][0],
                              pos[1] + window.pencilmark_offset[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if c_chain and cell_id in c_chain:
            for candidate, color in c_chain[cell_id]:
                if value == candidate:
                    pygame.draw.rect(window.screen, html_color_codes[color],
                                     (pos[0] + window.pencilmark_offset[value][0],
                                      pos[1] + window.pencilmark_offset[value][1],
                                      CELL_SIZE // 3, CELL_SIZE // 3))
        for chain in (chain_a, chain_b, chain_c, chain_d):
            if chain and cell_id in chain:
                for candidate, color in chain[cell_id]:
                    if value == candidate:
                        pygame.draw.rect(window.screen, html_color_codes[color],
                                         (pos[0] + window.pencilmark_offset[value][0],
                                          pos[1] + window.pencilmark_offset[value][1],
                                          CELL_SIZE // 3, CELL_SIZE // 3))
        if skyscraper and value == skyscraper[0] and cell_id in skyscraper[1:]:
            pygame.draw.rect(window.screen, html_color_codes["cyan"],
                             (pos[0] + window.pencilmark_offset[value][0],
                              pos[1] + window.pencilmark_offset[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if sue_de_coq and cell_id in sue_de_coq:
            pygame.draw.rect(window.screen, html_color_codes["cyan"],
                             (pos[0] + window.pencilmark_offset[value][0],
                              pos[1] + window.pencilmark_offset[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if eliminate and (value, cell_id) in eliminate:
            pygame.draw.rect(window.screen, html_color_codes['darkgray'],
                             (pos[0] + window.pencilmark_offset[value][0],
                              pos[1] + window.pencilmark_offset[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))


def clicked_widget_id(window):
    """ Return id of a clicked widget (button or cell) """
    for key, button in window.buttons.items():
        if button.being_pressed():
            return key
    mouse_pos = pygame.mouse.get_pos()
    for cell_id, cell_rect in window.board_cells.items():
        if cell_rect.collidepoint(mouse_pos):
            return cell_id + CELL_ID_OFFSET
    return None


def clue_btn_clicked(window, *args, **kwargs):
    """ action on pressing 'Clue' button """
    if window.buttons[pygame.K_c].is_active() and not window.buttons[pygame.K_c].is_pressed():
        window.buttons[pygame.K_c].set_pressed(True)
        window.buttons[pygame.K_c].draw(window.screen)
        window.buttons[pygame.K_p].set_pressed(False)
        window.buttons[pygame.K_p].draw(window.screen)


def pencil_mark_btn_clicked(window, _, board, *args, **kwargs):
    """ action on pressing 'Pencil mark' button """
    if window.buttons[pygame.K_p].is_active() and not window.buttons[pygame.K_p].is_pressed():
        window.buttons[pygame.K_p].set_pressed(True)
        window.buttons[pygame.K_p].draw(window.screen)
        window.buttons[pygame.K_c].set_pressed(False)
        window.buttons[pygame.K_c].draw(window.screen)
        set_remaining_candidates(board, solver_status)


def next_btn_clicked(window, *args, **kwargs):
    """ action on pressing 'Next' button """
    if window.buttons[pygame.K_m].is_active():
        window.buttons[pygame.K_m].press_and_release(window.screen, False)
        set_btn_status(window, True, (pygame.K_b,))
        window.calculate_next_clue = True
        window.wait = False


def hint_btn_clicked(window, *args, **kwargs):
    """ action on pressing 'Hint' button """
    if window.buttons[pygame.K_h].is_active():
        window.buttons[pygame.K_h].press_and_release(window.screen, False)
        set_btn_status(window, False, (pygame.K_b,))
        window.suggest_technique = True
        window.calculate_next_clue = True
        window.wait = False


def back_btn_clicked(window, _, board, **kwargs):
    """ action on clicking 'Back' button """
    if window.buttons[pygame.K_b].is_active():
        solver_status.restore_baseline(board, window)
        set_keyboard_status(window, True)
        if not window.solver_status.set_givens:
            set_btn_status(window, True)
        window.buttons[pygame.K_b].press_and_release(window.screen)
        window.wait = False


def solve_btn_clicked(window, *args, **kwargs):
    """ action on pressing 'Solve' button """
    window.selected_cell = None
    if window.selected_key:
        window.buttons[int(window.selected_key)].set_pressed(False)
        window.buttons[int(window.selected_key)].draw(window.screen)
    window.selected_key = None
    window.buttons[pygame.K_s].press_and_release(window.screen)
    set_btn_status(window, False)
    set_keyboard_status(window, False)
    window.show_solution_steps = False
    window.board_updated = True
    window.calculate_next_clue = True
    window.wait = False


def animate_btn_clicked(window, *args, **kwargs):
    """ action on pressing 'Animate' button """
    window.selected_cell = None
    if window.selected_key:
        window.buttons[int(window.selected_key)].set_pressed(False)
        window.buttons[int(window.selected_key)].draw(window.screen)
    window.selected_key = None
    window.buttons[pygame.K_a].press_and_release(window.screen)
    set_btn_status(window, False)
    set_keyboard_status(window, False)
    window.board_updated = True
    window.wait = False
    window.animate = True


def reset_btn_clicked(window, _, board, *args, **kwargs):
    """ action on clicking 'Reset' button """
    solver_status.reset(board)
    window.show_solution_steps = True
    window.inspect = window.peep
    window.solver_status.cells_solved.clear()
    window.options_visible.clear()
    # window.wrong_values.clear()
    window.show_wrong_values = True
    window.critical_error = None
    window.show_all_pencil_marks = False
    window.selected_cell = None
    if not window.solver_status.set_givens:
        set_btn_status(window, True)
        set_btn_status(window, False, (pygame.K_b,))
        set_btn_state(window, False)
        set_btn_state(window, True, (pygame.K_c, ))
    window.selected_key = None
    window.wait = False
    window.calculate_next_clue = False


def toggle_pencil_marks_btn_clicked(window, _, board, *args, **kwargs):
    """ action on pressing 'Toggle pencil marks' button - TODO: add the button """
    if not window.buttons[pygame.K_m].is_pressed():
        window.show_all_pencil_marks = not window.show_all_pencil_marks
        window.render_board(board, solver_tool="plain_board")
        pygame.display.update()
        window.wait = False
        window.board_updated = False


def toggle_highlight_digit(window, _, board, *args, **kwargs):
    """ action on selecting 'x' option """
    if not window.buttons[pygame.K_m].is_pressed():     # TODO !!!
        window.highlight_selected_digit = not window.highlight_selected_digit
        window.render_board(board, solver_tool="plain_board")
        pygame.display.update()
        window.wait = False
        window.board_update = False


def move_selected_cell_right(window, *args, **kwargs):
    """ move selected cell RIGHT """
    if window.selected_cell is not None:
        row_max_cell_id = (window.selected_cell // 9) * 9 + 8
        window.selected_cell = min(window.selected_cell + 1, row_max_cell_id)
        window.wait = False
        window.board_updated = True


def move_selected_cell_left(window, *args, **kwargs):
    """ move selected cell LEFT """
    if window.selected_cell is not None:
        row_min_cell_id = (window.selected_cell // 9) * 9
        window.selected_cell = max(window.selected_cell - 1, row_min_cell_id)
        window.wait = False
        window.board_updated = True


def move_selected_cell_up(window, *args, **kwargs):
    """ move selected cell UP """
    if window.selected_cell is not None:
        window.selected_cell = window.selected_cell - 9 if window.selected_cell > 8 else window.selected_cell
        window.wait = False
        window.board_updated = True


def move_selected_cell_down(window, *args, **kwargs):
    """ move selected cell DOWN """
    if window.selected_cell is not None:
        window.selected_cell = window.selected_cell + 9 if window.selected_cell < 72 else window.selected_cell
        window.wait = False
        window.board_updated = True


def defining_completed(window, _, board, *args, **kwargs):
    """ actions on selecting 'd' options: ends sudoku puzzle definition """
    if window.solver_status.set_givens:
        window.solver_status.set_givens = False
        reset_btn_clicked(window, _, board, *args, **kwargs)


def save_sudoku_definition_file(window, _, board, *args, **kwargs):
    """ Save sudoku definition file
    TODO:
    This is a mock implementation of the option
    """
    import os

    file_name = 'sudoku_xyz'
    f_name, ext = os.path.splitext(file_name)
    path, _ = os.path.split(file_name)
    if ext.lower() != '.txt':
        ext = '.txt'
    if not path:
        path = window.config["puzzles"]
    path_name = os.path.join(path, f_name+ext.lower())
    with open(path_name, "w") as sudoku_puzzle:
        for cell_id in range(81):
            cell_value = board[cell_id] + ',' if board[cell_id].isdigit() else '.,'
            sudoku_puzzle.write(cell_value)


def check_options_integrity(window, _, board, *args, **kwargs):
    """ check integrity of (entered) candidates """
    chain_i = defaultdict(set)
    for cell in window.options_visible:
        candidates = get_cell_candidates(cell, board, solver_status)
        if candidates != set(board[cell]):
            for value in candidates.symmetric_difference(set(board[cell])):
                chain_i[cell].add((value, 'pink'))
    if chain_i:
        solver_tool = "options_integrity_issue"
        set_btn_status(window, False, (pygame.K_h, pygame.K_m, pygame.K_s, pygame.K_b, pygame.K_a))
    else:
        solver_tool = "options_integrity_ok"
        # set_btn_status(window, True, (pygame.K_h, pygame.K_m, pygame.K_s, pygame.K_a))
    window.draw_board(board, solver_tool=solver_tool, chain_i=chain_i)
    pygame.display.update()
    window.wait = False
    window.board_updated = False


def quit_btn_clicked(window, *args, **kwargs):
    """ action on clicking 'Quit' button  """
    window.wait = False
    pygame.quit()
    sys.exit()


def keyboard_btn_clicked(window, btn_id, *args, **kwargs):
    """ Actions on pressing a keyboard button (in app window or on computer keyboard)
    """
    assert not (window.selected_cell and window.selected_key)

    if window.selected_cell is not None:
        window.value_entered = ValueEntered(window.selected_cell, str(btn_id),
                                            True if window.buttons[pygame.K_c].is_pressed() else False)
        window.wait = False
    else:
        if str(btn_id) == window.selected_key:
            window.selected_key = None
            window.buttons[btn_id].set_pressed(False)
            window.buttons[btn_id].draw(window.screen)
        else:
            if window.selected_key:
                window.buttons[int(window.selected_key)].set_pressed(False)
                window.buttons[int(window.selected_key)].draw(window.screen)
            window.selected_key = str(btn_id)
            window.buttons[btn_id].set_pressed(True)
            window.buttons[btn_id].draw(window.screen)

    # if window.highlight_selected_digit:
    # window.render_board(board, solver_tool="plain_board")
    # pygame.display.update()
    window.wait = False
    window.board_update = True


def cell_clicked(window, cell_id, *args, **kwargs):
    """ Actions on clicking a board cell
     - If a key is selected it is entered as cell given/clue/candidate
     - Otherwise, the cell is activated or deactivated (if it was active)
    """
    if get_keyboard_status(window):
        cell_id -= CELL_ID_OFFSET
        if window.solver_status.set_givens or cell_id not in solver_status.givens:
            if window.selected_key:
                window.value_entered = ValueEntered(cell_id, window.selected_key,
                                                    True if window.buttons[pygame.K_c].is_pressed() else False)
                # if window.buttons[pygame.K_c].is_pressed() and not window.solver_status.set_givens:
                #     window.buttons[int(window.selected_key)].set_pressed(False)
                #    window.buttons[int(window.selected_key)].draw(window.screen)
                #     window.selected_key = None
                # window.board_updated = True
            else:
                if cell_id == window.selected_cell:
                    window.selected_cell = None
                else:
                    window.selected_cell = cell_id
            window.wait = False


def set_buttons(window):
    """ set all button widgets and associated actions """
    btn_x = window.keypad_frame[0]
    btn_y = window.keypad_frame[1] + window.keypad_frame[3] + 15

    btn_rect = pygame.Rect((btn_x, btn_y, window.keypad_frame[3], BUTTON_H))
    window.buttons[pygame.K_c] = Button(pygame.K_c, btn_rect, "Clues", window.font_buttons)
    window.buttons[pygame.K_c].set_pressed(True)
    window.actions[pygame.K_c] = clue_btn_clicked

    btn_y += BUTTON_H + BUTTONS_OFFSET
    btn_rect = pygame.Rect((btn_x, btn_y, window.keypad_frame[3], BUTTON_H))
    window.buttons[pygame.K_p] = Button(pygame.K_p, btn_rect, "Pencil Marks", window.font_buttons)
    window.actions[pygame.K_p] = pencil_mark_btn_clicked

    btn_y += BUTTON_H + BUTTONS_OFFSET + 20
    # btn_w = (window.keypad_frame[3] - BUTTONS_OFFSET) // 2
    btn_rect = pygame.Rect((btn_x, btn_y, window.keypad_frame[3], BUTTON_H))
    window.buttons[pygame.K_h] = Button(pygame.K_h, btn_rect, "Hint", window.font_buttons)
    window.actions[pygame.K_h] = hint_btn_clicked
    
    btn_y += BUTTON_H + BUTTONS_OFFSET
    btn_w = (window.keypad_frame[3] - BUTTONS_OFFSET) // 2
    btn_rect = pygame.Rect((btn_x, btn_y, btn_w, BUTTON_H))
    window.buttons[pygame.K_m] = Button(pygame.K_m, btn_rect, "Move", window.font_buttons)
    window.actions[pygame.K_m] = next_btn_clicked

    btn_rect = pygame.Rect((btn_x + btn_w + BUTTONS_OFFSET, btn_y, btn_w, BUTTON_H))
    window.buttons[pygame.K_b] = Button(pygame.K_b, btn_rect, "Back", window.font_buttons)
    window.buttons[pygame.K_b].set_status(False)
    window.actions[pygame.K_b] = back_btn_clicked

    btn_y += BUTTON_H + BUTTONS_OFFSET
    btn_rect = pygame.Rect((btn_x, btn_y, window.keypad_frame[3], BUTTON_H))
    window.buttons[pygame.K_a] = Button(pygame.K_a, btn_rect, "Animate", window.font_buttons)
    window.actions[pygame.K_a] = animate_btn_clicked

    btn_y += BUTTON_H + BUTTONS_OFFSET
    btn_rect = pygame.Rect((btn_x, btn_y, window.keypad_frame[3], BUTTON_H))
    window.buttons[pygame.K_s] = Button(pygame.K_s, btn_rect, "Solve", window.font_buttons)
    window.actions[pygame.K_s] = solve_btn_clicked

    x_offset = LEFT_MARGIN + 9 * CELL_SIZE + KEYPAD_LEFT_MARGIN
    for row in range(3):
        for col in range(3):
            digit = 3 * row + col + 1
            btn_x = x_offset + col * (KEYPAD_DIGIT_W + KEYPAD_DIGIT_OFFSET)
            btn_y = KEYPAD_TOP_MARGIN + row * (KEYPAD_DIGIT_H + KEYPAD_DIGIT_OFFSET)
            btn_rect = pygame.Rect((btn_x, btn_y, KEYPAD_DIGIT_W, KEYPAD_DIGIT_H))
            window.buttons[digit] = Button(digit, btn_rect, str(digit), window.font_keypad)
            window.actions[digit] = keyboard_btn_clicked

    for cell_id in range(CELL_ID_OFFSET, CELL_ID_OFFSET + 81):
        window.actions[cell_id] = cell_clicked

    x_offset = LEFT_MARGIN
    y_offset = (TOP_MARGIN + 9 * CELL_SIZE)
    y_offset += (window_size()[1] - (TOP_MARGIN + 9 * CELL_SIZE) - BUTTON_H) // 2
    btn_rect = pygame.Rect((x_offset, y_offset, btn_w, BUTTON_H))
    window.buttons[pygame.K_q] = Button(pygame.K_q, btn_rect, "Quit", window.font_buttons)
    window.actions[pygame.K_q] = quit_btn_clicked

    x_offset += btn_w + 3 * BUTTONS_OFFSET
    btn_rect = pygame.Rect((x_offset, y_offset, btn_w, BUTTON_H))
    window.buttons[pygame.K_r] = Button(pygame.K_q, btn_rect, "Reset", window.font_buttons)
    window.actions[pygame.K_r] = reset_btn_clicked

    # TODO: These are hidden options; decide what to do with them
    window.actions[pygame.K_d] = defining_completed
    window.actions[pygame.K_o] = toggle_pencil_marks_btn_clicked
    window.actions[pygame.K_i] = check_options_integrity
    window.actions[pygame.K_w] = save_sudoku_definition_file
    window.actions[pygame.K_x] = toggle_highlight_digit
    window.actions[pygame.K_RIGHT] = move_selected_cell_right
    window.actions[pygame.K_LEFT] = move_selected_cell_left
    window.actions[pygame.K_UP] = move_selected_cell_up
    window.actions[pygame.K_DOWN] = move_selected_cell_down



def window_size():
    """ Return tuple defining window size """
    display_width = LEFT_MARGIN + 9 * CELL_SIZE + 2 * KEYPAD_LEFT_MARGIN + \
                    3 * KEYPAD_DIGIT_W + 2 * KEYPAD_DIGIT_OFFSET
    display_height = TOP_MARGIN + 9 * CELL_SIZE + BOTTOM_MARGIN
    win_size = (display_width, display_height)
    return win_size


def set_cell_rectangles():
    """ Set and return dictionary of cell rectangles """
    cell_rectangles = {row * 9 + col: pygame.Rect((col * CELL_SIZE + LEFT_MARGIN,
                                                   row * CELL_SIZE + TOP_MARGIN,
                                                   CELL_SIZE, CELL_SIZE))
                       for row in range(9) for col in range(9)}
    return cell_rectangles


def set_keypad_frame():
    """ Return keypad frame rectangle """
    x_offset = LEFT_MARGIN + 9 * CELL_SIZE + KEYPAD_LEFT_MARGIN - KEYPAD_TO_KEYS
    y_offset = KEYPAD_TOP_MARGIN - KEYPAD_TO_KEYS
    keyboard_w = 3 * (KEYPAD_DIGIT_W + KEYPAD_DIGIT_OFFSET) - KEYPAD_DIGIT_OFFSET + 2 * KEYPAD_TO_KEYS
    keyboard_h = 3 * (KEYPAD_DIGIT_H + KEYPAD_DIGIT_OFFSET) - KEYPAD_DIGIT_OFFSET + 2 * KEYPAD_TO_KEYS
    return pygame.Rect((x_offset, y_offset, keyboard_w, keyboard_h))


def set_keypad_keys():
    """ Set and return dictionary of keypad keys """
    keypad_keys = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3,
                   pygame.K_4: 4, pygame.K_5: 5, pygame.K_6: 6,
                   pygame.K_7: 7, pygame.K_8: 8, pygame.K_9: 9,
                   pygame.K_KP1: 1, pygame.K_KP2: 2, pygame.K_KP3: 3,
                   pygame.K_KP4: 4, pygame.K_KP5: 5, pygame.K_KP6: 6,
                   pygame.K_KP7: 7, pygame.K_KP8: 8, pygame.K_KP9: 9,
                   }
    return keypad_keys


def set_pencilmark_offset():
    """ Set and return dictionary of offsets for options display """
    return {'1': (0, 0),
            '2': (CELL_SIZE // 3, 0),
            '3': (2 * CELL_SIZE // 3, 0),
            '4': (0, CELL_SIZE // 3),
            '5': (CELL_SIZE // 3, CELL_SIZE // 3),
            '6': (2 * CELL_SIZE // 3, CELL_SIZE // 3),
            '7': (0, 2 * CELL_SIZE // 3),
            '8': (CELL_SIZE // 3, 2 * CELL_SIZE // 3),
            '9': (2 * CELL_SIZE // 3, 2 * CELL_SIZE // 3),
            }


def set_methods():
    """ Set and return dictionary of solver methods shortcuts """
    return {"full_house": "g",
            "visual_elimination": "v",
            "naked_single": "n",
            "hidden_single": "u",
            "unique_values": "u",
            "hidden_pairs": "h",    # TODO - obsolete!
            "hidden_pair": "h",
            "naked_pair": "p",
            "naked_twins": "p",     # TODO - obsolete!
            "omissions": "o",       # TODO - obsolete!
            "locked_candidates_type_1": "o",
            "locked_candidates_type_2": "o",
            "xy_wing": "y",
            "hidden_triplet": "i",
            "hidden_quad": "j",
            "naked_triplet": "t",
            "naked_quad": "q",
            "unique_rectangles": "r",
            "uniqueness_test_1": "r",
            "uniqueness_test_2": "r",
            "uniqueness_test_3": "r",
            "uniqueness_test_4": "r",
            "uniqueness_test_5": "r",
            "uniqueness_test_6": "r",
            "x_wing": "x",
            "finned_x_wing": "f",
            "finned_jellyfish": "9",
            "finned_squirmbag": "9",
            "franken_x_wing": "a",
            "finned_rccb_mutant_x_wing": "7",
            "finned_cbrc_mutant_x_wing": "8",
            "finned_rbcc_mutant_x_wing": "9",
            "sashimi_x_wing": "9",
            "sashimi_swordfish": "9",
            "sashimi_jellyfish": "9",
            "sashimi_squirmbag": "9",
            "skyscraper": "k",
            "swordfish": "s",
            "finned_swordfish": "w",
            "jellyfish": "l",
            "squirmbag": "6",
            "sue_de_coq": "q",
            "scrub_pencil_marks": "c",
            "iterate": "z",
            "plain_board": "b",
            "plain_board_file_info": "b",
            "options_integrity_issue": "b",
            "options_integrity_ok": "b",
            "manual_entry": "0",
            "xyz_wing": "1",
            "remote_pairs": "2",
            "wxy_wing": "3",
            "wxyz_wing_type_1": "4",
            "wxyz_wing_type_2": "4",
            "wxyz_wing_type_3": "4",
            "wxyz_wing_type_4": "4",
            "wxyz_wing_type_5": "4",
            "w_wing": "4",
            "empty_rectangle": "5",
            # "coloring": "6",
            "color_trap": "6",
            "color_wrap": "6",
            "multi_colors": "6",
            "multi_colors-color_wrap": "6",
            "multi_colors-color_wing": "6",
            # "x_colors": "6",
            "x_colors_elimination": "6",
            "x_colors_contradiction": "6",
            "three_d_medusa": "6",
            "naked_xy_chain": "9",
            "hidden_xy_chain": "9",
            "y_wings": "9",             # TODO!!!
            "almost_locked_candidates": "0",
            "als_xz": "0",
            "als_xy_wing": "0",
            "als_xy": "0",
            "death_blossom": "0",
            "two_string_kite": "0",
            }


def set_btn_status(window, active, btn_ids=None):
    """ Set status (active/inactive) of the provided buttons """
    if not btn_ids:
        btn_ids = window.buttons.keys()
    for button in btn_ids:
        window.buttons[button].set_status(active)
        window.buttons[button].draw(window.screen)
        pygame.display.update()


def set_btn_state(window, pressed, btn_ids=None):
    """ Set state (pressed/released) of the provided buttons """
    if not btn_ids:
        btn_ids = window.buttons.keys()
    for button in btn_ids:
        window.buttons[button].set_pressed(pressed)
        window.buttons[button].draw(window.screen)
        pygame.display.update()


def set_keyboard_status(window, status):
    """ Set status (active/inactive) of all keyboard keys """
    for key in range(1, 10):
        window.buttons[key].set_status(status)
        window.buttons[key].draw(window.screen)
        pygame.display.update()


def get_keyboard_status(window):
    """ Get keyboard status (True if active, False if disabled) """
    return window.buttons[1].is_active()

