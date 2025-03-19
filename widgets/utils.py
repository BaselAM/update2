import time
from PyQt5.QtGui import QColor


def is_dark_color(color_str):
    """Determine if a color is dark to ensure proper text contrast"""
    if not color_str:
        return True

    # Handle hex colors
    if color_str.startswith('#'):
        if len(color_str) == 7:  # #RRGGBB
            try:
                r = int(color_str[1:3], 16)
                g = int(color_str[3:5], 16)
                b = int(color_str[5:7], 16)
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                return brightness < 128
            except (ValueError, IndexError):
                return True
    return True