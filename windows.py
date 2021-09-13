import curses
import curses.textpad
import curses.ascii
import os
from typing import Optional

class WindowArea():
    def __init__(self, window_manager):
        self.pad = curses.newpad(0, 0)
        self.scroll_x = 0
        self.scroll_y = 0
        self.lines: list[str] = []

        self.display_width = 0
        self.display_height = 0
        self.display_x = 0
        self.display_y = 0
        self.cursor: Optional[Cursor] = None

        self.windows_manager = window_manager

    def get_width(self):
        # if len(self.lines) == 0:
        #     return 0
        longest_line = max([len(line) for line in self.lines])
        return longest_line + 1 # buffer of 1 character to the right so cursor can be positioned there

    def get_height(self):
        return len(self.lines)

    def draw(self, blinking_state: bool):
        if self.cursor is not None:
            self.cursor.draw_blinking(self, blinking_state)
        self.pad.refresh(self.scroll_y, self.scroll_x, self.display_y, self.display_x,
                self.display_y + min(self.display_height, self.get_height()),
                self.display_x + min(self.display_width, self.get_width()))

    def update_contents(self):
        if self.cursor is not None:
            self.cursor.ensure_in_bounds(self)

            self.scroll_x = max(self.cursor.x + 5 - self.display_width, 0)
            self.scroll_y = max(self.cursor.y + 5 - self.display_height, 0)

        self.pad.clear()
        self.pad.resize(self.get_height(), self.get_width())

        if len(self.lines) == 0:
            return

        y = 0
        for line in self.lines:
            self.pad.addstr(y, 0, line)
            y += 1

    def process_input(self, input) -> bool:
        pass

class FilenamesPrefixArea(WindowArea):
    def __init__(self, window_manager):
        super().__init__(window_manager)


class FilenamesArea(WindowArea):
    def __init__(self, window_manager):
        super().__init__(window_manager)

        self.line_paths: list[str] = []

        self.prefix_area = FilenamesPrefixArea(window_manager)


        self.state: int = 0

        self.state0_cursor: Cursor = None
        self.cursor: Cursor = None
        self.transition_to_state(0)

    def get_current_cursor(self):
        return self.cursor if self.state == 1 else self.state0_cursor

    def transition_to_state(self, new_state: int):
        self.state = new_state
        if new_state == 0:
            self.state0_cursor = self.cursor

            if self.state0_cursor is None:
                self.state0_cursor = Cursor()
            self.cursor = None
        elif new_state == 1:
            self.cursor = self.state0_cursor

            if self.cursor is None:
                self.cursor = Cursor()
            self.state0_cursor = None

    def draw(self, blinking_state):
        self.prefix_area.display_x = self.display_x
        self.prefix_area.display_y = self.display_y
        self.prefix_area.display_width = self.display_width
        self.prefix_area.display_height = self.display_height

        self.prefix_area.draw(blinking_state)

        # offset
        self.display_x += 4

        if self.state == 0:
            for x in range(0, self.get_width()):
                self.pad.chgat(self.state0_cursor.y, x, 1, curses.A_STANDOUT)

        super().draw(blinking_state)
        self.display_x -= 4

    def update_contents(self):
        self.prefix_area.update_contents()
        self.get_current_cursor().ensure_in_bounds(self)
        return super().update_contents()

    def read_folder(self, path: str):
        assert not os.path.isfile(path)

        self.lines = []
        self.line_paths = []
        self.prefix_area.lines = []
        for file in os.listdir(path):
            if not os.path.isfile(file):
                self.lines.append("./" + file)
                self.line_paths.append(os.path.join(path, file))
                self.prefix_area.lines.append("📁")

        file_number = 1
        for file in os.listdir(path):
            if os.path.isfile(file):
                self.lines.append(file)
                self.line_paths.append(os.path.join(path, file))
                self.prefix_area.lines.append(str(file_number))
                file_number += 1

        assert len(self.lines) > 0

        status_area = self.windows_manager.status_area

        if len(status_area.lines) == 0:
            status_area.lines.append("")
        status_area.lines[0] = path + " [{} {} found]".format(str(file_number), "files" if file_number > 0 else "file")

    def process_input(self, input) -> bool:
        if len(self.lines) == 0:
            return

        current_line = self.lines[self.get_current_cursor().y]

        if isinstance(input, int):
            # arrow keys
            if input == 258:
                self.get_current_cursor().y += 1
            elif input == 259:
                self.get_current_cursor().y -= 1
            elif input == 260:
                self.get_current_cursor().x -= 1
            elif input == 261:
                self.get_current_cursor().x += 1
            # delete
            elif input == 330:
                if len(current_line) > self.get_current_cursor().x:
                    current_line_list = list(current_line)
                    del current_line_list[self.get_current_cursor().x]
                    self.lines[self.get_current_cursor().y] = "".join(current_line_list)
            # f2
            elif input == 266:
                if self.state == 0:
                    self.transition_to_state(1)
        else:
            print("input info:\nstring ->{}<-\nbytes ->{}<-".format(str(input), str(bytes(input, 'utf-8'))))

            do_nothing_byte_inputs = [
                b'\t'
            ]

            if bytes(input, 'utf-8') == b'\n':
                self.read_folder(self.line_paths[self.get_current_cursor().y])
                return False
            elif bytes(input, 'utf-8') in do_nothing_byte_inputs:
                print("do nothing")
                return False
            elif bytes(input, 'utf-8') == b'\x08': # backspace
                if self.get_current_cursor().x == 0:
                    return False
                current_line_list = list(current_line)
                del current_line_list[self.get_current_cursor().x - 1]
                self.lines[self.get_current_cursor().y] = "".join(current_line_list)
                self.get_current_cursor().x -= 1
                return False

            current_line_list = list(current_line)
            current_line_list.insert(self.get_current_cursor().x, input)

            self.lines[self.get_current_cursor().y] = "".join(current_line_list)
            self.get_current_cursor().x += 1

        return False

class Cursor():
    def __init__(self):
        self.x = 0
        self.y = 0
        pass

    def ensure_in_bounds(self, window: WindowArea):
        assert len(window.lines) > 0, "Empty lines!"

        if self.y >= len(window.lines):
            self.y = len(window.lines) - 1
        elif self.y < 0:
            self.y = 0

        current_line = window.lines[self.y]

        if self.x > len(current_line):
            self.x = len(current_line)
        elif self.x < 0:
            self.x = 0

    def draw_blinking(self, window: WindowArea, blinking_state: bool):
        window.pad.chgat(self.y, self.x, 1, curses.A_NORMAL if not blinking_state else curses.A_BLINK)
