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

# blinking right after user input
SHORT_BLINKING = 300

# blinking during timeouts
NORMAL_BLINKING = 500

def is_close_input(input):
    if isinstance(input, int):
        return False

    exit_byte_inputs = [
        b'\x03', b'\x1b'
    ]
    return bytes(input, 'utf-8') in exit_byte_inputs

class WindowManager():
    def start(self, main_window):
        self.main_window = main_window

        self.filenames_area = FilenamesArea(self)
        self.status_area = WindowArea(self)

        self.input_focus_area: WindowArea = self.filenames_area
        self.all_windows = [self.status_area, self.filenames_area]

        self.close_application = False
        self.blinking_state: bool = True

        curses.curs_set(0)
        main_window.nodelay(1)

        print("Window size is... w: {}, h: {}".format(str(get_width()), str(get_height())))

        main_window.timeout(SHORT_BLINKING)


        self.filenames_area.read_folder(os.getcwd())

        self.resize_windows()
        self.update()
        self.draw()

        while not self.close_application:
            try:
                input = main_window.get_wch()

                if is_close_input(input):
                    print("closed")
                    self.close_application = True
                    continue
                elif input == 546:
                    self.resize_windows()
                    self.draw()
                    continue

                self.input_focus_area.process_input(input)

                self.blinking_state = True
                self.update()
                self.draw()
                main_window.timeout(SHORT_BLINKING)
            except curses.error: # timeout while waiting for user input
                # TODO narrow 'except' down so I only catch the timeout error
                self.blinking_state = not self.blinking_state
                self.update()
                self.draw()
                main_window.timeout(NORMAL_BLINKING)

    def update(self):
        for win in self.all_windows:
            win.update_contents()

    def draw(self):
        self.main_window.refresh()
        for win in self.all_windows:
            win.draw(self.blinking_state)

    def resize_windows(self):
        self.status_area.display_x = 0
        self.status_area.display_y = 0
        self.status_area.display_width = get_width()
        self.status_area.display_height = 1

        self.filenames_area.display_x = 0
        self.filenames_area.display_y = 1
        self.filenames_area.display_width = int(get_width() / 2)
        self.filenames_area.display_height = get_height()

        print("width: {}".format(str(self.filenames_area.display_width)))

if __name__ == '__main__':
    curses.wrapper(WindowManager().start)