import curses
import curses.textpad
import curses.ascii
import os
from pathlib import Path
import threading
import time

lines: list[str] = []
line_paths: list[Path] = []

close_application = False

class Cursor():
    def __init__(self):
        self.x = 0
        self.y = 0
        pass

    def ensure_in_bounds(self):
        assert len(lines) > 0, "Empty lines!"

        if self.y >= len(lines):
            self.y = len(lines) - 1
        elif self.y < 0:
            self.y = 0

        current_line = lines[self.y]

        if self.x > len(current_line):
            self.x = len(current_line)
        elif self.x < 0:
            self.x = 0

        global window

cursor: Cursor = Cursor()

window: curses.window = None

def get_width():
    return curses.COLS

def get_height():
    return curses.LINES

def refresh():
    window.clear()
    y = 0
    for line in lines:
        window.addstr(y, 0, line)
        y += 1

    window.chgat(cursor.y, cursor.x, 1, curses.A_BLINK)
    window.refresh()

def process_write_input(input):
    global close_application

    if isinstance(input, int):
        pass
    else:
        print("input info:\nstring ->{}<-\nbytes ->{}<-".format(str(input), str(bytes(input, 'utf-8'))))

        do_nothing_byte_inputs = [
            b'\t'
        ]

        cursor.ensure_in_bounds()
        current_line = lines[cursor.y]

        # pressed escape?
        if bytes(input, 'utf-8') == b'\x1b':
            print("closed")
            close_application = True
            return
        elif bytes(input, 'utf-8') == b'\n':
            cursor.y += 1
            cursor.ensure_in_bounds()
            return
        elif bytes(input, 'utf-8') in do_nothing_byte_inputs:
            print("do nothing")
            return
        elif bytes(input, 'utf-8') == b'\x08': # backspace
            if cursor.x == 0:
                return
            current_line_list = list(current_line)
            del current_line_list[cursor.x - 1]
            lines[cursor.y] = "".join(current_line_list)
            cursor.x -= 1
            return

        current_line_list = list(current_line)
        current_line_list.insert(cursor.x, input)

        lines[cursor.y] = "".join(current_line_list)
        cursor.x += 1

def read_folder(path: str):
    global lines
    global lines_paths

    assert not os.path.isfile(path)

    lines = []
    line_paths = []
    for file in os.listdir(path):
        if not os.path.isfile(file):
            lines.append("./" + file)
            line_paths.append(os.path.join(path, file))

    for file in os.listdir(path):
        if os.path.isfile(file):
            lines.append(file)
            line_paths.append(os.path.join(path, file))

    assert len(lines) > 0

def main(new_window):
    global window
    window = new_window
    window.clear()

    print("w: {}, h: {}".format(str(get_width()), str(get_height())))

    curses.curs_set(0)

    read_folder(os.getcwd())

    cursor.ensure_in_bounds()
    refresh()

    blinking_state = False
    SHORT_BLINKING = 300
    NORMAL_BLINKING = 500

    window.timeout(SHORT_BLINKING)
    while not close_application:
        try:
            char = window.get_wch()
            process_write_input(char)
            refresh()
            blinking_state = False
            window.timeout(SHORT_BLINKING)
        except Exception:
            print("blink")
            window.chgat(cursor.y, cursor.x, 1, curses.A_NORMAL if not blinking_state else curses.A_BLINK)
            window.refresh()
            blinking_state = not blinking_state
            window.timeout(NORMAL_BLINKING)

curses.wrapper(main)