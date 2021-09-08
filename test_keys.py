import curses
import curses.textpad
import curses.ascii

def main(new_window: curses.window):
    while True:
        char = new_window.getch()

        new_window.addstr("char: {}, int: {}, bytes: {}, type: {}\n".format(chr(char), str(char), bytes(chr(char), 'utf-8'), type(char)))

        if chr(char) == '\x1b':
            return

if __name__ == '__main__':
    curses.wrapper(main)