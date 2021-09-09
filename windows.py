import curses
import curses.textpad
import curses.ascii
import os

class WindowArea():
    def __init__(self):
        self.pad = curses.newpad(0, 0)
        self.scroll_x = 0
        self.scroll_y = 0
        self.lines: list[str] = []

        self.display_width = 0
        self.display_height = 0
        self.display_x = 0
        self.display_y = 0

    def draw(self):
        self.pad.refresh(self.scroll_y, self.scroll_x, self.display_y, self.display_x,
                min(self.display_height, self.get_height()),
                min(self.display_width, self.get_width()))

    def get_width(self):
        longest_line = max([len(line) for line in self.lines])
        return longest_line + 1 # buffer of 1 character in the right so cursor can be positioned there

    def get_height(self):
        return len(self.lines)


class FilenamesArea(WindowArea):
    def __init__(self):
        super().__init__()

        self.line_paths: list[str] = []

    def update_contents(self):
        self.pad.clear()
        if len(self.lines) == 0:
            return

        self.pad.resize(self.get_height(), self.get_width())

        y = 0
        for line in self.lines:
            self.pad.addstr(y, 0, line)
            y += 1

    def read_folder(self, path: str):
        assert not os.path.isfile(path)

        self.lines = []
        self.line_paths = []
        for file in os.listdir(path):
            if not os.path.isfile(file):
                self.lines.append("./" + file)
                self.line_paths.append(os.path.join(path, file))

        for file in os.listdir(path):
            if os.path.isfile(file):
                self.lines.append(file)
                self.line_paths.append(os.path.join(path, file))

        assert len(self.lines) > 0

    def process_write_input(self, cursor, input) -> bool:
        if len(self.lines) == 0:
            return

        current_line = self.lines[cursor.y]

        if isinstance(input, int):
            # arrow keys
            if input == 258:
                cursor.y += 1
            elif input == 259:
                cursor.y -= 1
            elif input == 260:
                cursor.x -= 1
            elif input == 261:
                cursor.x += 1
            # delete
            elif input == 330:
                if len(current_line) > cursor.x:
                    current_line_list = list(current_line)
                    del current_line_list[cursor.x]
                    self.lines[cursor.y] = "".join(current_line_list)
        else:
            print("input info:\nstring ->{}<-\nbytes ->{}<-".format(str(input), str(bytes(input, 'utf-8'))))

            do_nothing_byte_inputs = [
                b'\t'
            ]

            if bytes(input, 'utf-8') == b'\n':
                cursor.y += 1
                return False
            elif bytes(input, 'utf-8') in do_nothing_byte_inputs:
                print("do nothing")
                return False
            elif bytes(input, 'utf-8') == b'\x08': # backspace
                if cursor.x == 0:
                    return False
                current_line_list = list(current_line)
                del current_line_list[cursor.x - 1]
                self.lines[cursor.y] = "".join(current_line_list)
                cursor.x -= 1
                return False

            current_line_list = list(current_line)
            current_line_list.insert(cursor.x, input)

            self.lines[cursor.y] = "".join(current_line_list)
            cursor.x += 1

        return False

class Cursor():
    def __init__(self):
        self.x = 0
        self.y = 0
        pass

    def ensure_in_bounds(self, window: WindowArea):
        # assert len(window.lines) > 0, "Empty lines!"
        if len(window.lines) == 0:
            return

        if self.y >= len(window.lines):
            self.y = len(window.lines) - 1
        elif self.y < 0:
            self.y = 0

        current_line = window.lines[self.y]

        if self.x > len(current_line):
            self.x = len(current_line)
        elif self.x < 0:
            self.x = 0