import curses
import curses.textpad
import curses.ascii

lines: list[str] = []

close_application = False

class Cursor():
    def __init__(self):
        self.x = 0
        self.y = 0
        pass

    def ensure_in_bounds(self):
        current_line = get_current_line()
        if self.x > len(current_line):
            self.x = len(current_line)
        elif self.x < 0:
            self.x = 0

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

def get_current_line() -> str:
    while not(0 <= cursor.y < len(lines)):
        lines.append("")
    return lines[cursor.y]

def process_input(input):
    global close_application

    if isinstance(input, int):
        pass
    else:
        print("input info:\nstring ->{}<-\nbytes ->{}<-".format(str(input), str(bytes(input, 'utf-8'))))

        do_nothing_byte_inputs = [
            b'\t'
        ]

        current_line = get_current_line()
        cursor.ensure_in_bounds()

        # pressed escape?
        if bytes(input, 'utf-8') == b'\x1b':
            print("closed")
            close_application = True
            return
        elif bytes(input, 'utf-8') == b'\n':
            cursor.y += 1
            get_current_line()
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


def main(new_window):
    global window
    window = new_window
    window.clear()

    print("w: {}, h: {}".format(str(get_width()), str(get_height())))

    while not close_application:
        char = window.get_wch()
        process_input(char)
        window.move(cursor.y, cursor.x)
        refresh()

curses.wrapper(main)