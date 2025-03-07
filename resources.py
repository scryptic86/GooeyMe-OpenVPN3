from gi.repository import Gtk, GdkPixbuf
import os

class Resources:
    _icons_loaded = False
    
    @classmethod
    def load_icons(cls):
        if cls._icons_loaded: return
        
        icon_theme = Gtk.IconTheme.get_default()
        base_path = os.path.dirname(__file__)
        
        icons = [
            ("openvpn-connected", "icons/connected.png"),
            ("openvpn-disconnected", "icons/disconnected.png")
        ]
        
        for name, path in icons:
            full_path = os.path.join(base_path, path)
            if os.path.exists(full_path):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(full_path)
                icon_theme.add_builtin_icon(name, 24, pixbuf)
        
        cls._icons_loaded = True