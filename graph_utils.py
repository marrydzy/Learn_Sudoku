import time
import sys
import pygame

from solver_manual import solver_status
from solver_manual import init_options
from utils import is_solved
from display import screen_messages


ANIMATION_STEP_TIME = 0.05
CELL_ID_OFFSET = 1000

# dimensions of sudoku board:
CELL_SIZE = 66
LEFT_MARGIN = 25
TOP_MARGIN = 60
BOTTOM_MARGIN = 90

# RGB colors:
BLACK = (0, 0, 0)
BLUE = (51, 102, 153)
CORAL = (255, 127, 80)
CYAN = (0, 255, 255)
DARKGREY = (120, 120, 120)
GAINSBORO = (230, 230, 230)
GREY = (160, 160, 160)
LIME = (0, 255, 0)
MAGENTA = (255, 0, 255)
RED = (255, 0, 0)
SILVER = (192, 192, 192)
WHITE = (255, 255, 255)

LIGHTGREEN = (190, 255, 190)
LIENGHTPINK = (255, 182, 193)
LIGHTYELLOW = (255, 255, 224)
LIGHTGREY = (200, 200, 200)
LIGHTCORAL = (255, 120, 120)

C_BTN_BORDER = (153, 189, 173)
C_BTN_FACE = (198, 200, 200)
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
                 border_color=C_BTN_BORDER, face_color=C_BTN_FACE, font_color=(50, 50, 50),
                 disable_border_color=LIGHTGREY, disable_face_color=WHITE, disable_font_color=GAINSBORO,
                 pressed_border_color=C_PRESSED_BTN_BORDER, pressed_face_color=C_PRESSED_BTN_BORDER,
                 pressed_font_color=WHITE):
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
    if cell not in window.show_options:
        if "impacted_cells" in kwargs and cell in kwargs["impacted_cells"]:
            window.show_options.add(cell)
        if "claims" in kwargs and cell in kwargs["house"]:
            window.show_options.add(cell)
        if "y_wing" in kwargs and kwargs["y_wing"] and cell in kwargs["y_wing"][1:]:
            window.show_options.add(cell)
    return True if cell in window.show_options else False


def render_clue(window, clue, pos, color):
    """ Render board clue """
    digit = window.font_clues.render(clue, True, color)
    window.screen.blit(digit, (pos[0] + window.clue_shift_x, pos[1] + window.clue_shift_y))


def render_options(window, cell_id, pos):
    """ Render cell options (pencil marks) """
    options = window.input_board[cell_id]
    for value in options:
        digit = window.font_options.render(value, True, BLACK)
        window.screen.blit(digit, (pos[0] + window.option_offsets[value][0] + window.option_shift_x,
                           pos[1] + window.option_offsets[value][1] + window.option_shift_y))


def cell_color(window, cell, **kwargs):
    """ TODO """
    color = WHITE
    if "house" in kwargs and kwargs["house"] and cell in kwargs["house"]:
        color = LIGHTYELLOW
    if "greyed_out" in kwargs and kwargs["greyed_out"] and cell in kwargs["greyed_out"]:
        color = SILVER
    if "conflicted_cells" in kwargs and kwargs["conflicted_cells"] and cell in kwargs["conflicted_cells"]:
        color = LIGHTCORAL
    if "impacted_cells" in kwargs and kwargs["impacted_cells"] and cell in kwargs["impacted_cells"]:
        color = C_OTHER_CELLS
    if cell == window.selected_cell or \
            "new_clue" in kwargs and kwargs["new_clue"] and cell == kwargs["new_clue"]:
        color = LIGHTGREEN
    if window.critical_error and cell in window.critical_error:
        color = LIGHTCORAL
    return color


def display_info(window, text):
    """ Display info 'text' starting at the left top corner of the window """
    if text:
        msg = window.font_text.render(text, True, BLACK)
        top_margin = (TOP_MARGIN - window.font_text.get_ascent()) // 2
        info_rect = pygame.Rect((LEFT_MARGIN, top_margin, 9 * CELL_SIZE, window.font_text_size+1))
        pygame.draw.rect(window.screen, GAINSBORO, info_rect)
        window.screen.set_clip(info_rect)
        window.screen.blit(msg, (LEFT_MARGIN, top_margin))
        window.screen.set_clip(None)


def draw_keypad(window):
    """ TODO """
    pygame.draw.rect(window.screen, DARKGREY, window.keypad_frame, width=1, border_radius=9)


def draw_board_features(window, **kwargs):
    """ TBD """

    rectangle = kwargs["rectangle"] if "rectangle" in kwargs else None
    y_wing = kwargs["y_wing"] if "y_wing" in kwargs else None
    x_wing = kwargs["x_wing"] if "x_wing" in kwargs else None

    if rectangle:
        left = (rectangle[0] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        top = (rectangle[0] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        right = (rectangle[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        bottom = (rectangle[2] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        rect = pygame.Rect(left, top, right - left, bottom - top)
        pygame.draw.rect(window.screen, MAGENTA, rect, width=4)

    if x_wing:
        color = MAGENTA
        x_wing = sorted(x_wing[1:])
        x1 = (x_wing[0] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y1 = (x_wing[0] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        x2 = (x_wing[3] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y2 = (x_wing[3] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        pygame.draw.line(window.screen, color, (x1, y1), (x2, y2), width=5)
        x1 = (x_wing[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y1 = (x_wing[1] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        x2 = (x_wing[2] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y2 = (x_wing[2] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        pygame.draw.line(window.screen, color, (x1, y1), (x2, y2), width=5)

    if y_wing:
        x1 = (y_wing[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y1 = (y_wing[1] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        root = (x1, y1)
        x2 = (y_wing[2] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y2 = (y_wing[2] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        leaf = (x2, y2)
        width = 4 if x1 == x2 or y1 == y2 else 5
        pygame.draw.line(window.screen, MAGENTA, root, leaf, width=width)
        x2 = (y_wing[3] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
        y2 = (y_wing[3] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
        leaf = (x2, y2)
        width = 4 if x1 == x2 or y1 == y2 else 5
        pygame.draw.line(window.screen, MAGENTA, root, leaf, width=width)


def highlight_options(window, cell_id, new_value, pos, **kwargs):
    """ Highlight pencil marks, as applicable """

    remove = kwargs["remove"] if "remove" in kwargs else None
    claims = kwargs["claims"] if "claims" in kwargs else None
    iterate = kwargs["iterate"] if "iterate" in kwargs else None
    y_wing = kwargs["y_wing"] if "y_wing" in kwargs else None
    corners = kwargs["rectangle"] if "rectangle" in kwargs else None
    x_wing = kwargs["x_wing"] if "x_wing" in kwargs else None
    sword = kwargs["sword"] if "sword" in kwargs else None

    if iterate is not None and cell_id == iterate:
        pygame.draw.rect(
            window.screen, LIENGHTPINK,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if y_wing is not None and cell_id == y_wing[1]:
        pygame.draw.rect(
            window.screen, Y_WING_ROOT,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if y_wing is not None and (cell_id == y_wing[2] or cell_id == y_wing[3]):
        pygame.draw.rect(
            window.screen, Y_WING_LEAF,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if corners and cell_id in corners or x_wing and cell_id in x_wing[1:]:
        pygame.draw.rect(
            window.screen, Y_WING_LEAF,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
    if sword and cell_id in sword[1:]:
        pygame.draw.rect(
            window.screen, Y_WING_LEAF,
            (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))

    for value in window.input_board[cell_id]:
        if remove and (value, cell_id) in remove:
            pygame.draw.rect(window.screen, GREY,
                             (pos[0] + window.option_offsets[value][0],
                              pos[1] + window.option_offsets[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))

        if claims and value in new_value and cell_id in claims:
            pygame.draw.rect(window.screen, CYAN,
                             (pos[0] + window.option_offsets[value][0],
                              pos[1] + window.option_offsets[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if claims and (value, cell_id) in claims:
            pygame.draw.rect(window.screen, CYAN,
                             (pos[0] + window.option_offsets[value][0],
                              pos[1] + window.option_offsets[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if x_wing and value == x_wing[0] and cell_id in x_wing[1:]:
            pygame.draw.rect(window.screen, CYAN,
                             (pos[0] + window.option_offsets[value][0],
                              pos[1] + window.option_offsets[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if y_wing and value == y_wing[0] and cell_id in (y_wing[2], y_wing[3]):
            pygame.draw.rect(window.screen, CYAN,
                             (pos[0] + window.option_offsets[value][0],
                              pos[1] + window.option_offsets[value][1],
                              CELL_SIZE // 3, CELL_SIZE // 3))
        if sword and value == sword[0] and cell_id in sword[1:]:
            pygame.draw.rect(window.screen, CYAN,
                             (pos[0] + window.option_offsets[value][0],
                              pos[1] + window.option_offsets[value][1],
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


def pencil_mark_btn_clicked(window, *args, **kwargs):
    """ action on pressing 'Pencil mark' button """
    if window.buttons[pygame.K_p].is_active() and not window.buttons[pygame.K_p].is_pressed():
        window.buttons[pygame.K_p].set_pressed(True)
        window.buttons[pygame.K_p].draw(window.screen)
        window.buttons[pygame.K_c].set_pressed(False)
        window.buttons[pygame.K_c].draw(window.screen)


def hint_btn_clicked(window, btn_id, board, solver_tool, **kwargs):
    """ action on pressing 'Hint' button """
    if window.buttons[pygame.K_h].is_active():
        window.buttons[pygame.K_h].set_pressed(True)
        set_btn_status(window, True, (pygame.K_a, pygame.K_b))
        set_btn_status(window, False, (pygame.K_c, pygame.K_p, pygame.K_m, pygame.K_s))
        set_keyboard_status(window, False)
        window.render_board(board, solver_tool, **kwargs)
        display_info(window, screen_messages[solver_tool])


def back_btn_clicked(window, btn_id, board, solver_tool, **kwargs):
    """ action on clicking 'Back' button """
    window.buttons[pygame.K_h].set_pressed(False)
    set_btn_status(window, False, (pygame.K_a, pygame.K_b))
    set_btn_status(window, True, (pygame.K_c, pygame.K_p, pygame.K_m, pygame.K_s))
    set_keyboard_status(window, True)
    window.wait = False
    window.board_updated = False
    window.render_board(window.input_board, "plain_board")  # options_set=kwargs["options_set"])
    display_info(window, "")
    pygame.display.update()


def accept_btn_clicked(window, *args, **kwargs):
    """ action on clicking 'Accept' button """
    if window.buttons[pygame.K_a].is_active():
        window.buttons[pygame.K_h].set_pressed(False)
        set_btn_status(window, False, (pygame.K_b, pygame.K_a))
        set_btn_status(window, True, (pygame.K_c, pygame.K_p, pygame.K_m, pygame.K_s))
        set_keyboard_status(window, True)
        window.board_updated = True
        window.wait = False


def solve_btn_clicked(window, *args, **kwargs):
    """ action on pressing 'Solve' button """
    window.buttons[pygame.K_s].set_pressed(True)
    set_btn_status(window, False, (pygame.K_c, pygame.K_p, pygame.K_a, pygame.K_h, pygame.K_b, pygame.K_m))
    set_keyboard_status(window, False)
    window.show_solution_steps = False
    window.board_updated = True
    window.wait = False


def animate_btn_clicked(window, btn_id, board, solver_tool, **kwargs):
    """ action on pressing 'Animate' button """
    window.buttons[pygame.K_m].set_pressed(True)
    set_btn_status(window, False, (pygame.K_c, pygame.K_p, pygame.K_a, pygame.K_h,
                                   pygame.K_b, pygame.K_m, pygame.K_s, pygame.K_r))
    set_keyboard_status(window, False)
    window.animate = True
    window.wait = False
    window.board_updated = True
    window.render_board(board, solver_tool, **kwargs)
    time.sleep(ANIMATION_STEP_TIME)


def reset_btn_clicked(window, _, board, *args, **kwargs):
    """ action on clicking 'Reset' button """
    solver_status.reset(board, window)
    window.show_solution_steps = True
    window.inspect = window.peep
    window.clues_found.clear()
    window.show_options.clear()
    window.critical_error = None
    window.show_all_pencil_marks = False
    set_btn_status(window, True)
    set_btn_status(window, False, (pygame.K_b, pygame.K_a))
    set_btn_state(window, False)
    set_btn_state(window, True, (pygame.K_c, ))
    window.selected_key = None
    window.wait = False
    for i in range(81):     # TODO temporary needed due to mix with old solver
        if i not in window.clues_defined:
            board[i] = "."
    window.board_updated = False


def toggle_pencil_marks_btn_clicked(window, _, board, *args, **kwargs):
    """ action on pressing 'Toggle pencil marks' button - TODO: add the button """
    if not window.buttons[pygame.K_h].is_pressed():
        init_options(board, window)
        window.show_all_pencil_marks = not window.show_all_pencil_marks
        window.render_board(window.input_board, "plain_board")
        pygame.display.update()
        window.wait = False
        window.board_updated = True


def quit_btn_clicked(window, *args, **kwargs):
    """ action on clicking 'Quit' button - TODO: add the button  """
    window.wait = False
    pygame.quit()
    sys.exit()


def keyboard_btn_clicked(window, btn_id, *args, **kwargs):
    """ action on pressing a keyboard button """
    if window.selected_cell:
        window.clue_entered = (window.selected_cell, str(btn_id))
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
    window.selected_cell = None


def cell_clicked(window, cell_id, *args, **kwargs):
    """ action on clicking a board cell """
    cell_id -= CELL_ID_OFFSET
    if cell_id not in window.clues_defined:
        if window.selected_key:
            window.clue_entered = (cell_id, window.selected_key)
            if window.solved_board[cell_id] == window.selected_key:
                window.appraisal = 'You are a genius !!!'
            else:
                window.appraisal = 'You are an idiot !!!'
            window.wait = False
        else:
            if cell_id == window.selected_cell:
                window.selected_cell = None
            else:
                window.selected_cell = cell_id
            window.render_board(window.input_board, "plain_board")
            pygame.display.update()


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
    btn_w = (window.keypad_frame[3] - BUTTONS_OFFSET) // 2
    btn_rect = pygame.Rect((btn_x, btn_y, btn_w, BUTTON_H))
    window.buttons[pygame.K_h] = Button(pygame.K_h, btn_rect, "Hint", window.font_buttons)
    window.actions[pygame.K_h] = hint_btn_clicked

    btn_rect = pygame.Rect((btn_x + btn_w + BUTTONS_OFFSET, btn_y, btn_w, BUTTON_H))
    window.buttons[pygame.K_b] = Button(pygame.K_b, btn_rect, "Back", window.font_buttons)
    window.buttons[pygame.K_b].set_status(False)
    window.actions[pygame.K_b] = back_btn_clicked

    btn_y += BUTTON_H + BUTTONS_OFFSET
    btn_rect = pygame.Rect((btn_x, btn_y, window.keypad_frame[3], BUTTON_H))
    window.buttons[pygame.K_a] = Button(pygame.K_a, btn_rect, "Accept", window.font_buttons)
    window.buttons[pygame.K_a].set_status(False)
    window.actions[pygame.K_a] = accept_btn_clicked

    btn_y += BUTTON_H + BUTTONS_OFFSET
    btn_rect = pygame.Rect((btn_x, btn_y, window.keypad_frame[3], BUTTON_H))
    window.buttons[pygame.K_m] = Button(pygame.K_m, btn_rect, "Animate", window.font_buttons)
    window.actions[pygame.K_m] = animate_btn_clicked

    btn_y += BUTTON_H + BUTTONS_OFFSET
    btn_rect = pygame.Rect((btn_x, btn_y, window.keypad_frame[3], BUTTON_H))
    window.buttons[pygame.K_s] = Button(pygame.K_s, btn_rect, "Auto Solve", window.font_buttons)
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

    window.actions[pygame.K_p] = toggle_pencil_marks_btn_clicked  # TODO - add buttons


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


def set_option_offsets():
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
    return {"open_singles": "g",
            "visual_elimination": "v",
            "naked_singles": "n",
            "hidden_singles": "u",
            "unique_values": "u",
            "hidden_pairs": "h",
            "naked_twins": "p",
            "omissions": "o",
            "y_wings": "y",
            "hidden_triplets": "i",
            "hidden_quads": "j",
            "naked_triplets": "t",
            "naked_quads": "q",
            "unique_rectangles": "r",
            "x_wings": "x",
            "swordfish": "s",
            "iterate": "z",
            }


def set_btn_status(window, active, btn_ids=None):
    """ Set status (active/inactive) of the provided buttons """
    if not btn_ids:
        btn_ids = window.buttons.keys()
    for button in btn_ids:
        window.buttons[button].set_status(active)


def set_btn_state(window, pressed, btn_ids=None):
    """ Set state (pressed/released) of the provided buttons """
    if not btn_ids:
        btn_ids = window.buttons.keys()
    for button in btn_ids:
        window.buttons[button].set_pressed(pressed)


def set_keyboard_status(window, status):
    """ Set status (active/inactive) of all keyboard keys """
    for id in range(1, 10):
        window.buttons[id].set_status(status)