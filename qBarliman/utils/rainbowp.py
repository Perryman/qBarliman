# There's probably a library or builtin for this but this is more fun.
def esc(c, s) -> str:
    return f"\033[{c}m{s}\033[0m"


def cmp(*args) -> str:
    return ";".join(map(str, args))


def col(s, *args) -> str:  # splat args in case of multiple codes
    args = args[0] if len(args) == 1 and isinstance(args[0], (list, tuple)) else args
    return esc(cmp(*args), str(s))


T_RESET = 0
T_BOLD = 1
T_BRIGHT = 1
T_REVERSE = 7
T_FRAMED = 51
T_ENCIRCLED = 52

T_BLACK = 30
T_RED = 31
T_GREEN = 32
T_YELLOW = 33
T_BLUE = 34
T_MAGENTA = 35
T_CYAN = 36
T_WHITE = 37

# aixterm bright fg
T_BRIGHT_BLACK = 90
T_BRIGHT_RED = 91
T_BRIGHT_GREEN = 92
T_BRIGHT_YELLOW = 93
T_BRIGHT_BLUE = 94
T_BRIGHT_MAGENTA = 95
T_BRIGHT_CYAN = 96
T_BRIGHT_WHITE = 97


# Terminal version (ANSI escape codes):
def rainbowp(text):
    PCOLORS = [
        (T_REVERSE, T_BRIGHT_WHITE),
        T_GREEN,
        T_YELLOW,
        T_BLUE,
        T_MAGENTA,
        T_CYAN,
        T_BRIGHT_GREEN,
        T_BRIGHT_YELLOW,
        T_BRIGHT_BLUE,
        T_BRIGHT_MAGENTA,
        T_BRIGHT_CYAN,
    ]

    color_index = 0
    total_count = 0

    output = ""
    for char in text:
        if char in "([{":
            color = PCOLORS[color_index % len(PCOLORS)]
            output += col(char, color)
            color_index += 1
            total_count += 1
        elif char in ")]}":
            if color_index > 0:
                color_index -= 1
                color = PCOLORS[color_index % len(PCOLORS)]
                output += col(char, color)
            else:
                output += col(char, T_BRIGHT_RED)  # unmatched
        elif char in "$":
            output += col(char, T_BRIGHT_RED, T_REVERSE)
        else:
            output += char

    return output
