import threading
import os
import sys
import pystray
from PIL import Image, ImageDraw, ImageFont
def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)
def load_app_icon():
    try:
        return Image.open(resource_path("icon.png")).convert("RGBA").resize((64, 64))
    except (OSError, FileNotFoundError):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        ImageDraw.Draw(img).rounded_rectangle((0, 0, 63, 63), radius=12, fill=(90, 90, 90))
        return img
APP_ICON = load_app_icon()
def bgcolor(level, charging):
    if charging:
        return (60, 130, 255)
    if level < 20:
        return (220, 50, 50)
    if level < 50:
        return (240, 170, 30)
    return (60, 200, 90)
def make_icon(level, charging=False):
    if level is None:
        return APP_ICON.copy()
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, 63, 63), radius=15, fill=bgcolor(level, charging))
    text = str(level)
    try:
        font = ImageFont.truetype("segoeuib.ttf", 34 if len(text) < 3 else 26)
    except OSError:
        font = ImageFont.load_default()
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text(((64 - (r - l)) / 2 - l, (64 - (b - t)) / 2 - t), text, font=font, fill="white")
    return img
def icon_text(level, charging=False, name=None):
    if name is None :
        return "HAxon"
    
    if level is None:
        return f"HAxon: {name}"
    return f"{name} battery: {level}%" + (" (charging)" if charging else "")
class tray_icon:
    def __init__(self, root, on_quit):
        self.root = root
        self.on_quit = on_quit
        self.icon = None
    def restore(self, *_):
        self.root.after(0, self.do_restore)
    def do_restore(self):
        self.stop()
        self.root.deiconify()
        self.root.lift()
    def quit(self, *_):
        self.root.after(0, self.on_quit)
    def start(self, level, charging=False, name=None):
        if self.icon:
            return
        self.root.withdraw()
        menu = pystray.Menu(
            pystray.MenuItem("Open Axon", self.restore, default=True),
            pystray.MenuItem("Close Axon", self.quit),
        )
        self.icon = pystray.Icon("Axon", make_icon(level, charging), icon_text(level, charging, name), menu)
        threading.Thread(target=self.icon.run, daemon=True).start()
    def update(self, level, charging=False, name= None):
        if self.icon:
            self.icon.icon = make_icon(level, charging)
            self.icon.title = icon_text(level, charging, name)
    def stop(self):
        if self.icon:
            self.icon.stop()
            self.icon = None