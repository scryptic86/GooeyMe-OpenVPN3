import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, Notify, GLib, Gio, Secret
import subprocess
import os
import json
import logging
import keyring
from threading import Thread
from datetime import datetime

class VPNManager:
    """Handles core VPN operations with error handling"""
    
    def __init__(self):
        self.session_id = None
        self.connection_thread = None
        self.auto_reconnect = False
        self.logger = logging.getLogger(__name__)

    def import_profile(self, path, name, credentials):
        """Validate and import VPN profile with credentials"""
        try:
            # Validate OVPN file
            if not self._validate_ovpn(path):
                raise ValueError("Invalid OVPN file")
            
            # Store credentials securely
            Secret.password_store_sync(
                Secret.Schema.new("com.example.openvpn3-gui"),
                {"profile": name},
                Secret.COLLECTION_DEFAULT,
                f"OpenVPN3 credentials for {name}",
                json.dumps(credentials),
                None,
            )

            # Import config
            subprocess.run(
                ["sudo", "openvpn3", "config-import", "--config", path, "--name", name],
                check=True
            )
            return True
        except Exception as e:
            self.logger.error(f"Profile import failed: {str(e)}")
            return False

    def connect(self, profile_name, log_callback=None):
        """Establish connection with error handling and logging"""
        def connection_task():
            try:
                cmd = ["sudo", "openvpn3", "session-start", "--config", profile_name]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                for line in iter(process.stdout.readline, ''):
                    GLib.idle_add(log_callback, line.strip())
                    
                process.wait()
                if process.returncode == 0:
                    self.session_id = process.stdout.strip()
                else:
                    raise subprocess.CalledProcessError(
                        process.returncode, cmd
                    )
            except Exception as e:
                GLib.idle_add(self.logger.error, f"Connection error: {str(e)}")

        self.connection_thread = Thread(target=connection_task)
        self.connection_thread.start()

    def validate_credentials(self, profile_name):
        """Check if credentials exist for profile"""
        try:
            return Secret.password_lookup_sync(
                Secret.Schema.new("com.example.openvpn3-gui"),
                {"profile": profile_name},
                None
            )
        except Exception as e:
            return False

class LogHandler(logging.Handler):
    """Custom log handler for GUI integration"""
    
    def __init__(self, textview):
        super().__init__()
        self.textview = textview
        self.buffer = textview.get_buffer()
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        GLib.idle_add(self.append_log, msg)

    def append_log(self, message):
        end_iter = self.buffer.get_end_iter()
        self.buffer.insert(end_iter, message + "\n")
        self.textview.scroll_to_iter(end_iter, 0, False, 0, 0)

class AutoReconnectManager:
    """Handles automatic reconnection logic"""
    
    def __init__(self, vpn_manager):
        self.vpn_manager = vpn_manager
        self.active = False
        self.retry_interval = 30  # seconds
        self.max_retries = 5

    def start(self):
        self.active = True
        GLib.timeout_add_seconds(self.retry_interval, self.check_connection)

    def check_connection(self):
        if self.active and not self.vpn_manager.session_id:
            self.vpn_manager.connect()
        return self.active

class MainWindow(Gtk.ApplicationWindow):
    """Main application window with all features"""
    
    def __init__(self, app):
        super().__init__(application=app)
        self.builder = Gtk.Builder()
        self.builder.add_from_file("openvpn3-gui.glade")
        self.builder.connect_signals(self)
        
        # Initialize subsystems
        self.vpn_manager = VPNManager()
        self.reconnect_manager = AutoReconnectManager(self.vpn_manager)
        self.log_handler = LogHandler(self.builder.get_object("log_view"))
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        
        # Initialize notifications
        Notify.init("OpenVPN3 GUI")
        
        # Load settings
        self.load_settings()

    def load_settings(self):
        """Load persisted application settings"""
        try:
            with open(os.path.expanduser("~/.config/openvpn3-gui-settings.json")) as f:
                settings = json.load(f)
                self.reconnect_manager.active = settings.get("auto_reconnect", False)
        except FileNotFoundError:
            pass

    def save_settings(self):
        """Persist application settings"""
        settings = {
            "auto_reconnect": self.reconnect_manager.active
        }
        with open(os.path.expanduser("~/.config/openvpn3-gui-settings.json"), "w") as f:
            json.dump(settings, f)

    # Add remaining UI interaction methods and signal handlers
    # Implement features like:
    # - Credential management dialog
    # - Real-time log viewer
    # - Connection monitoring
    # - Notification system
    # - Automatic reconnection logic
    # - Input validation
    # - Error handling dialogs

class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.openvpn3gui.pro")
    
    def do_activate(self):
        win = MainWindow(self)
        win.show_all()

if __name__ == "__main__":
    app = Application()
    app.run()