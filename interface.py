"""Curses-based user interface."""

import curses
import signal
import string
import textwrap
from queue import SimpleQueue

KEYS = {
    # Printable comes first, so characters like 'tab' can be overridden below.
    "printable": [ord(letter) for letter in string.printable],
    "backspace": [8, 127, curses.KEY_BACKSPACE],
    "enter": [10, 13, curses.KEY_ENTER],
    "resize": [curses.KEY_RESIZE],
    "esc": [27],
    "kill": [4],  # Ctrl-D
    "discard": [
        9,  # Tab
        90,  # Shift-Tab
        353,  # Shift-Tab
        258,  # Down
        336,  # Shift-Down
        523,  # Alt-Down
        524,  # Alt-Shift-Down
        525,  # Ctrl-Down
        526,  # Ctrl-Shift-Down
        259,  # Up
        337,  # Shift-Up
        564,  # Alt-Up
        565,  # Alt-Shift-Up
        566,  # Ctrl-Up
        567,  # Ctrl-Shift-Up
        260,  # Left
        393,  # Shift-Left
        543,  # Alt-Left
        544,  # Alt-Shift-Left
        545,  # Ctrl-Left
        546,  # Ctrl-Shift-Left
        261,  # Right
        402,  # Shift-Right
        558,  # Alt-Right
        559,  # Alt-Shift-Right
        560,  # Ctrl-Right
        561,  # Ctrl-Shift-Right
        330,  # Del
        383,  # Shift-Del
        517,  # Alt-Del
        518,  # Alt-Shift-Del
        519,  # Ctrl-Del
        520,  # Ctrl-Shift-Del
        331,  # Ins
        538,  # Alt-Ins
        262,  # Home
        391,  # Shift-Home
        533,  # Alt-Home
        534,  # Alt-Shift-Home
        535,  # Ctrl-Home
        536,  # Ctrl-Shift-Home
        360,  # End
        386,  # Shift-End
        528,  # Alt-End
        529,  # Alt-Shift-End
        530,  # Ctrl-End
        531,  # Ctrl-Shift-End
        339,  # PgUp
        398,  # Shift-PgUp
        553,  # Alt-PgUp
        554,  # Alt-Shift-PgUp
        338,  # PgDn
        396,  # Shift-PgDn
        548,  # Alt-PgDn
        549,  # Alt-Shift-PgDn
    ],
}


class UserInterface:
    """The user interface."""

    def __init__(self):
        """Initialize the User Interface."""
        self.active = False
        self.buffer = {
            "input": str(),
            "output": list(),
        }
        self.keymap = dict()
        for (key, values) in KEYS.items():
            for value in values:
                self.keymap[value] = key
        self.layout = {
            "out_frame": {
                "parent": "base",
                "size": (-3, 0),
                "position": (0, 0),
                "border": True,
            },
            "output": {
                "parent": "out_frame",
                "size": (-2, -2),
                "position": (1, 1),
                "border": False,
            },
            "in_frame": {
                "parent": "base",
                "size": (3, 0),
                "position": (-3, 0),
                "border": True,
            },
            "input": {
                "parent": "in_frame",
                "size": (1, -4),
                "position": (1, 3),
                "border": False,
            },
        }
        self.prompt = "> "
        self.queues = {
            "input": SimpleQueue(),
            "output": SimpleQueue(),
        }
        self.window = dict()

    @staticmethod
    def _get_subwin(screen, size=(0, 0), pos=(0, 0)):
        """Return a sub-window of the specified screen."""
        (row, col) = pos
        (rows, cols) = size
        (top, left) = screen.getbegyx()
        (max_rows, max_cols) = screen.getmaxyx()
        row += top if abs(row) == row else max_rows
        col += left if abs(col) == col else max_cols
        rows += max_rows if abs(rows) != rows or rows == 0 else 0
        cols += max_cols if abs(cols) != cols or cols == 0 else 0
        return screen.subwin(rows, cols, row, col)

    def _handle_input(self):
        """Handle new input."""
        old_buf = str(self.buffer["input"])
        # Process new input.
        key = self.window["base"].getch()
        if key != -1:
            self._handle_key(key)
        # Redraw the window if necessary.
        if old_buf != self.buffer["input"]:
            self._redraw_input()

    def _handle_key(self, key):
        """Handle a specific key."""
        funcmap = {
            "backspace": self._key_backspace,
            "discard": self._key_discard,
            "enter": self._key_enter,
            "esc": self._key_esc,
            "kill": self._key_kill,
            "none": self._key_undefined,
            "printable": self._key_printable,
            "resize": self._key_resize,
        }
        func = funcmap.get(self.keymap.get(key, "none"), self._key_undefined)
        func(key)

    def _handle_output(self):
        """Handle new output."""
        redraw = False
        # Check for new output.
        if not self.queues["output"].empty():
            message = self.queues["output"].get()
            if message.lower() == ";quit":
                self.active = False
            else:
                self.buffer["output"].append(message)
                redraw = True
        # Redraw the window if necessary.
        if redraw:
            self._redraw_output()

    def _key_backspace(self, key):
        """Handle the backspace key."""
        self.buffer["input"] = self.buffer["input"][:-1]
        return key

    def _key_enter(self, key):
        """Handle the enter key."""
        self.queues["input"].put(self.buffer["input"])
        self.buffer["input"] = str()
        return key

    def _key_esc(self, key):
        """Handle the escape key."""
        self.buffer["input"] = str()
        return key

    def _key_kill(self, key):
        """Handle the kill keys."""
        self.active = False
        return key

    def _key_printable(self, key):
        """Add the character to the buffer."""
        self.buffer["input"] += chr(key)
        return key

    def _key_resize(self, key):
        """Handle window resize."""
        try:
            self._redraw_windows()
        except curses.error:
            self.active = False
        return key

    @staticmethod
    def _key_discard(key):
        """Discard the key."""
        return key

    def _key_undefined(self, key):
        """Handle unknown key."""
        # While testing, we'll show the int value of the key.
        # In production, we'll simply drop the key.
        self.buffer["input"] += f"(?{key})"
        return key

    def _launch_interface(self, stdscr):
        """Set up curses and start the main loop."""
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self.window["base"] = stdscr
        self.window["base"].nodelay(True)
        self.window["base"].timeout(25)
        self._redraw_windows()
        self._main_loop()

    def _main_loop(self):
        """Execute main loop."""
        self.active = True
        while self.active:
            try:
                if curses.is_term_resized(*self.window["base"].getmaxyx()):
                    self._redraw_windows()
                curses.doupdate()
                self._handle_input()
                self._handle_output()
            except curses.error:
                self.active = False

    def _redraw_input(self):
        """Redraw the input window."""
        (_, max_buffer) = self.window["input"].getmaxyx()
        value = self.buffer["input"][-1 * (max_buffer - 2) :]
        self.window["input"].clear()
        self.window["input"].addstr(0, 0, value)
        self.window["input"].addstr(0, len(value), " ", curses.color_pair(1))
        self.window["input"].noutrefresh()

    def _redraw_output(self):
        """Redraw the output window."""
        self.window["output"].clear()
        (max_rows, max_cols) = self.window["output"].getmaxyx()
        output_lines = list()
        for line in self.buffer["output"][::-1]:
            output_lines += textwrap.wrap(line, max_cols)[::-1]
            if len(output_lines) >= max_rows:
                break
        for index, line in enumerate(output_lines[:max_rows]):
            if len(line) >= max_cols and index == 0:
                self.window["output"].insch(
                    max_rows - 1, max_cols - 1, line[max_cols - 1 :][0]
                )
                line = line[: max_cols - 1]
            self.window["output"].addstr(max_rows - (index + 1), 0, line)
        self.window["output"].noutrefresh()

    def _redraw_windows(self):
        """Redraw the window layout."""
        try:
            self.window["base"].clear()
            for name, layout in self.layout.items():
                self.window[name] = self._get_subwin(
                    self.window[layout["parent"]],
                    size=layout["size"],
                    pos=layout["position"],
                )
                if layout["border"]:
                    self.window[name].box()
            self.window["in_frame"].addstr(1, 1, self.prompt)
            self._redraw_input()
            self._redraw_output()
            for _, window in self.window.items():
                window.noutrefresh()
        except curses.error:
            self.active = False

    def _signal_handler(self, sig, frame):
        """Handle the Ctrl-C key sequence gracefully."""
        if sig == signal.SIGINT:
            # Frame used below to prevent pylint complaining.
            self.active = frame and False
        elif sig == signal.SIGQUIT:
            pass

    def get_io(self):
        """Return the input/output queues."""
        return (self.queues["input"], self.queues["output"])

    def launch(self):
        """Launch the user interface."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGQUIT, self._signal_handler)
        curses.wrapper(self._launch_interface)
