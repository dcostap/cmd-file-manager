import curses
import curses.textpad
import curses.ascii
import os
from pathlib import Path
import threading
import time
from windows import *

def get_width():
    return curses.COLS

def get_height():
    return curses.LINES

def main(main_window):
    close_application = False

    cursor: Cursor = Cursor()

    main_window.clear()
    curses.curs_set(0)
    main_window.nodelay(1)

    filenames_area: FilenamesArea = None
    filenames_area = FilenamesArea()
    filenames_area.read_folder(os.getcwd())

    active_area: WindowArea = filenames_area

    print("Window size is... w: {}, h: {}".format(str(get_width()), str(get_height())))

    blinking_state = False

    # blinking right after user input
    SHORT_BLINKING = 300

    # blinking during timeouts
    NORMAL_BLINKING = 500

    main_window.timeout(SHORT_BLINKING)

    def refresh_windows():
        main_window.refresh()
        filenames_area.refresh(cursor)

    def is_close_input(input):
        if isinstance(input, int):
            return False

        exit_byte_inputs = [
            b'\x03', b'\x1b'
        ]
        return bytes(input, 'utf-8') in exit_byte_inputs

    def resize_windows():
        filenames_area.display_x = 0
        filenames_area.display_y = 0
        filenames_area.display_width = int(get_width() / 2)
        filenames_area.display_height = get_height()

    resize_windows()

    while not close_application:
        try:
            input = main_window.get_wch()

            if is_close_input(input):
                print("closed")
                close_application = True
                break

            cursor.ensure_in_bounds(active_area)
            active_area.process_write_input(cursor, input)
            cursor.ensure_in_bounds(active_area)
            refresh_windows()
            blinking_state = False
            main_window.timeout(SHORT_BLINKING)
        except curses.error: # TODO narrow it down so I only catch the timeout error
            # timeout while waiting for user input
            refresh_windows()
            cursor.ensure_in_bounds(active_area)
            if len(active_area.lines) > 0:
                active_area.pad.chgat(cursor.y, cursor.x, 1, curses.A_NORMAL if not blinking_state else curses.A_BLINK)
            blinking_state = not blinking_state
            main_window.timeout(NORMAL_BLINKING)

if __name__ == '__main__':
    curses.wrapper(main)