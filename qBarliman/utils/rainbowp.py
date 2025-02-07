from enum import Enum

T_BLACK = "\033[30m"
T_RED = "\033[1;31m"
T_GREEN = "\033[32m"
T_YELLOW = "\033[33m"
T_BLUE = "\033[34m"
T_MAGENTA = "\033[35m"
T_CYAN = "\033[36m"
T_WHITE = "\033[37m"

T_BRIGHT_BLACK = "\033[90m"
T_BRIGHT_RED = "\033[1;91m"
T_BRIGHT_GREEN = "\033[92m"
T_BRIGHT_YELLOW = "\033[93m"
T_BRIGHT_BLUE = "\033[94m"
T_BRIGHT_MAGENTA = "\033[95m"
T_BRIGHT_CYAN = "\033[96m"
T_BRIGHT_WHITE = "\033[97m"

T_RESET = "\033[0m"  # Reset ANSI code


# Terminal version (ANSI escape codes):
def rainbowp(text):
    COLORS = [
        T_WHITE,
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
            color = COLORS[color_index % len(COLORS)]
            output += color + char + T_RESET
            color_index += 1
            total_count += 1
        elif char in ")]}":
            if color_index > 0:
                color_index -= 1
                color = COLORS[color_index % len(COLORS)]
                output += color + char + T_RESET
            else:
                output += T_RED + char + T_RESET  # unmatched
        else:
            output += char

    return output
