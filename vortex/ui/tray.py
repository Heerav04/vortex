import logging
import threading
from typing import Callable

import pystray
from PIL import Image, ImageDraw


def _create_icon() -> Image.Image:
    # Simple circular icon with a V in the middle.
    img = Image.new("RGB", (64, 64), color=(25, 25, 35))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), outline=(0, 200, 255), width=3)
    draw.text((22, 18), "V", fill=(0, 200, 255))
    return img


def start_tray(on_quit: Callable[[], None]) -> None:
    """
    Starts a system tray icon with a Quit option.
    Should be called from the main thread.
    """

    def _quit(icon, _item):
        logging.info("Tray quit clicked.")
        on_quit()
        icon.stop()

    menu = pystray.Menu(pystray.MenuItem("Quit Vortex", _quit))
    icon = pystray.Icon("Vortex", _create_icon(), "Vortex", menu)

    t = threading.Thread(target=icon.run, daemon=True)
    t.start()


__all__ = ["start_tray"]

