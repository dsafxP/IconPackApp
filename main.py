import shutil
import sys
import curses
import threading
import time
from pathlib import Path
import platform
from typing import Set, List, Tuple
from PIL import Image
import config


class CursesApp:
    def __init__(self):
        self.model = IconInstallerModel()
        self.stdscr = None
        self.current_screen = "main"
        self.selected_games: Set[int] = set()
        self.notifications: List[Tuple[str, float]] = []
        self.notification_lock = threading.Lock()

        # Add input buffer for path editing
        self.input_buffer = ""
        self.cursor_pos = 0

        # Steam path setup
        if platform.system() == "Windows":
            self.common_path = Path(r"C:\Program Files (x86)\Steam")
        elif platform.system() == "Linux":
            self.common_path = Path.home() / ".local" / "share" / "Steam"
        else:
            self.common_path = Path("")

    def run(self):
        curses.wrapper(self._main)

    def _main(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)  # Hide cursor

        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Header
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Selected
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Success
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)  # Error
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Info

        while True:
            self._draw_screen()
            if not self._handle_input():
                break

    def _draw_screen(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        # Draw header
        header_text = f"{config.NAME} - {time.strftime('%H:%M:%S')}"
        self.stdscr.addstr(0, 0, header_text.ljust(w), curses.color_pair(1))

        # Draw notifications
        self._draw_notifications()

        if self.current_screen == "main":
            self._draw_main_screen()
        elif self.current_screen == "style":
            self._draw_style_screen()
        elif self.current_screen == "games":
            self._draw_games_screen()
        elif self.current_screen == "confirm":
            self._draw_confirm_screen()
        elif self.current_screen == "path_input":
            self._draw_path_input_screen()

        # Draw footer
        self.stdscr.addstr(h - 1, 0, config.CREDITS[:w - 1], curses.color_pair(6))

        self.stdscr.refresh()

    def _draw_notifications(self):
        h, w = self.stdscr.getmaxyx()
        current_time = time.time()

        with self.notification_lock:
            # Remove expired notifications
            self.notifications = [(msg, exp) for msg, exp in self.notifications if exp > current_time]

            # Draw active notifications
            for i, (msg, _) in enumerate(self.notifications[-5:]):  # Show last 5
                color = curses.color_pair(3) if "✅" in msg else curses.color_pair(
                    4) if "❌" in msg else curses.color_pair(5)
                self.stdscr.addstr(2 + i, 2, msg[:w - 4], color)

    def _draw_main_screen(self):
        h, w = self.stdscr.getmaxyx()
        start_y = 8

        title = "STEAM ICON INSTALLER"
        self.stdscr.addstr(start_y, (w - len(title)) // 2, title, curses.A_BOLD)

        options = [
            "1. Apply Icons",
            "2. Select Style"
        ]

        # Add Extract Icons option if running as PyInstaller bundle
        if getattr(sys, 'frozen', False):
            options.insert(2, "3. Extract Icons")

        for i, option in enumerate(options):
            self.stdscr.addstr(start_y + 3 + i, (w - len(option)) // 2, option)

        self.stdscr.addstr(h - 3, 2, "Press number key to select option, 'q' to quit")

    def _draw_style_screen(self):
        h, w = self.stdscr.getmaxyx()
        start_y = 8

        title = "SELECT STYLE"
        self.stdscr.addstr(start_y, (w - len(title)) // 2, title, curses.A_BOLD)

        for i, style_name in enumerate(self.model.styles, 1):
            option = f"{i}. {style_name}"
            if i == self.model.current_style:
                option += " (CURRENT)"
                self.stdscr.addstr(start_y + 2 + i, (w - len(option)) // 2, option, curses.color_pair(2))
            else:
                self.stdscr.addstr(start_y + 2 + i, (w - len(option)) // 2, option)

        self.stdscr.addstr(h - 3, 2, "Press number to select style, 'b' to go back")

    def _draw_games_screen(self):
        h, w = self.stdscr.getmaxyx()
        start_y = 8

        title = "SELECT GAMES"
        self.stdscr.addstr(start_y, (w - len(title)) // 2, title, curses.A_BOLD)

        path_text = f"Steam Path: {self.common_path}"
        self.stdscr.addstr(start_y + 2, 2, path_text[:w - 4])

        # Get available games
        allowed = set(self.model.get_available_games())
        available_games = []

        for idx, (name, _, target_rel, _) in self.model.game_mapping.items():
            if idx in allowed:
                full_target = self.common_path / target_rel
                if full_target.parent.is_dir():
                    available_games.append((idx, name))

        # Draw games list
        self.stdscr.addstr(start_y + 4, 2, "Available Games:")
        for i, (game_id, name) in enumerate(available_games[:h - 15]):
            status = "[X]" if game_id in self.selected_games else "[ ]"
            line = f"{i + 1:2d}. {status} {name}"
            color = curses.color_pair(2) if game_id in self.selected_games else 0
            self.stdscr.addstr(start_y + 6 + i, 4, line[:w - 6], color)

        # Draw controls
        controls = [
            "Number: Toggle game selection",
            "a: Select/deselect all",
            "p: Change path",
            "Enter: Apply selected games",
            "b: Go back"
        ]

        for i, control in enumerate(controls):
            self.stdscr.addstr(h - 6 + i, 2, control)

    def _draw_confirm_screen(self):
        h, w = self.stdscr.getmaxyx()

        # Draw dialog box
        dialog_h, dialog_w = 7, 50
        start_y = (h - dialog_h) // 2
        start_x = (w - dialog_w) // 2

        # Draw box
        for y in range(start_y, start_y + dialog_h):
            for x in range(start_x, start_x + dialog_w):
                if y == start_y or y == start_y + dialog_h - 1:
                    self.stdscr.addch(y, x, curses.ACS_HLINE)
                elif x == start_x or x == start_x + dialog_w - 1:
                    self.stdscr.addch(y, x, curses.ACS_VLINE)
                else:
                    self.stdscr.addch(y, x, ' ')

        # Draw corners
        self.stdscr.addch(start_y, start_x, curses.ACS_ULCORNER)
        self.stdscr.addch(start_y, start_x + dialog_w - 1, curses.ACS_URCORNER)
        self.stdscr.addch(start_y + dialog_h - 1, start_x, curses.ACS_LLCORNER)
        self.stdscr.addch(start_y + dialog_h - 1, start_x + dialog_w - 1, curses.ACS_LRCORNER)

        # Draw content
        message = f"Apply icons to {len(self.selected_games)} games?"
        self.stdscr.addstr(start_y + 2, start_x + (dialog_w - len(message)) // 2, message)

        self.stdscr.addstr(start_y + 4, start_x + 8, "y: Confirm")
        self.stdscr.addstr(start_y + 4, start_x + 25, "n: Cancel")

    def _draw_path_input_screen(self):
        h, w = self.stdscr.getmaxyx()
        start_y = h // 2 - 5

        # Title
        title = "EDIT STEAM PATH"
        self.stdscr.addstr(start_y, (w - len(title)) // 2, title, curses.A_BOLD)

        # Instructions
        self.stdscr.addstr(start_y + 2, 2, "Current path:")
        self.stdscr.addstr(start_y + 3, 4, str(self.common_path), curses.color_pair(6))

        self.stdscr.addstr(start_y + 5, 2, "New path:")

        # Input field with border
        input_y = start_y + 6
        input_x = 4
        input_width = w - 8

        # Draw input box border
        self.stdscr.addch(input_y - 1, input_x - 1, curses.ACS_ULCORNER)
        self.stdscr.addch(input_y - 1, input_x + input_width, curses.ACS_URCORNER)
        self.stdscr.addch(input_y + 1, input_x - 1, curses.ACS_LLCORNER)
        self.stdscr.addch(input_y + 1, input_x + input_width, curses.ACS_LRCORNER)

        for x in range(input_x, input_x + input_width):
            self.stdscr.addch(input_y - 1, x, curses.ACS_HLINE)
            self.stdscr.addch(input_y + 1, x, curses.ACS_HLINE)

        for y in range(input_y, input_y + 1):
            self.stdscr.addch(y, input_x - 1, curses.ACS_VLINE)
            self.stdscr.addch(y, input_x + input_width, curses.ACS_VLINE)

        # Clear input area
        self.stdscr.addstr(input_y, input_x, " " * input_width)

        # Display input text
        display_text = self.input_buffer
        if len(display_text) > input_width - 1:
            # Scroll text if too long
            if self.cursor_pos < input_width // 2:
                display_text = display_text[:input_width - 1]
                display_cursor = self.cursor_pos
            else:
                start_pos = self.cursor_pos - input_width // 2
                display_text = display_text[start_pos:start_pos + input_width - 1]
                display_cursor = input_width // 2
        else:
            display_cursor = self.cursor_pos

        self.stdscr.addstr(input_y, input_x, display_text[:input_width - 1])

        # Position cursor
        cursor_x = min(input_x + display_cursor, input_x + input_width - 1)
        self.stdscr.move(input_y, cursor_x)

        # Controls
        controls = [
            "Enter: Confirm and validate path",
            "Escape: Cancel and return",
            "Ctrl+A: Move to beginning",
            "Ctrl+E: Move to end",
            "Ctrl+U: Clear input",
            "Home/End: Move cursor",
            "Backspace/Delete: Remove characters"
        ]

        for i, control in enumerate(controls):
            if start_y + 9 + i < h - 1:
                self.stdscr.addstr(start_y + 9 + i, 2, control[:w - 4])

        # Show cursor for input
        curses.curs_set(1)

    def _handle_input(self):
        try:
            key = self.stdscr.getch()
        except KeyboardInterrupt:
            return False

        if self.current_screen == "main":
            return self._handle_main_input(key)
        elif self.current_screen == "style":
            return self._handle_style_input(key)
        elif self.current_screen == "games":
            return self._handle_games_input(key)
        elif self.current_screen == "confirm":
            return self._handle_confirm_input(key)
        elif self.current_screen == "path_input":
            return self._handle_path_input(key)

        return True

    def _handle_main_input(self, key):
        if key == ord('q'):
            return False

        elif key == ord('1'):
            self.current_screen = "games"
        elif key == ord('2'):
            self.current_screen = "style"
        elif key == ord('3') and getattr(sys, 'frozen', False):
            self._extract_icons()

        return True

    def _handle_style_input(self, key):
        if key == ord('b'):
            self.current_screen = "main"
        elif ord('1') <= key <= ord('9'):
            style_num = key - ord('0')
            if 1 <= style_num <= len(self.model.styles):
                self.model.current_style = style_num
                self.notify(f"Style changed to {self.model.styles[style_num - 1]}")

        return True

    def _handle_games_input(self, key):
        if key == ord('b'):
            self.current_screen = "main"
        elif key == ord('p'):
            # Initialize input buffer with current path when entering path input
            self.input_buffer = str(self.common_path)
            self.cursor_pos = len(self.input_buffer)
            self.current_screen = "path_input"
        elif key == ord('a'):
            self._toggle_all_games()
        elif key == ord('\n') or key == ord('\r'):
            if self.selected_games:
                self.current_screen = "confirm"
            else:
                self.notify("No games selected!")
        elif ord('1') <= key <= ord('9'):
            self._toggle_game_by_number(key - ord('0'))

        return True

    def _handle_confirm_input(self, key):
        if key == ord('y'):
            self.current_screen = "games"
            self._apply_icons_threaded()
        elif key == ord('n'):
            self.current_screen = "games"

        return True

    def _handle_path_input(self, key):
        if key == ord('\n') or key == ord('\r'):  # Enter
            # Validate and confirm path
            if self.input_buffer.strip():
                new_path = Path(self.input_buffer.strip())
                if self._validate_steam_path(new_path):
                    self.common_path = new_path
                    self.notify(f"✅ Steam path updated: {new_path}")
                    self.current_screen = "games"
                    self._reset_input_buffer()
                else:
                    self.notify("❌ Invalid Steam path! Please check the directory.", 5.0)
            else:
                self.notify("❌ Path cannot be empty!")

        elif key == 27:  # Escape
            self.current_screen = "games"
            self._reset_input_buffer()

        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
            if self.cursor_pos > 0:
                self.input_buffer = (self.input_buffer[:self.cursor_pos - 1] +
                                     self.input_buffer[self.cursor_pos:])
                self.cursor_pos -= 1

        elif key == curses.KEY_DC:  # Delete
            if self.cursor_pos < len(self.input_buffer):
                self.input_buffer = (self.input_buffer[:self.cursor_pos] +
                                     self.input_buffer[self.cursor_pos + 1:])

        elif key == curses.KEY_LEFT:  # Left arrow
            if self.cursor_pos > 0:
                self.cursor_pos -= 1

        elif key == curses.KEY_RIGHT:  # Right arrow
            if self.cursor_pos < len(self.input_buffer):
                self.cursor_pos += 1

        elif key == curses.KEY_HOME or key == 1:  # Home or Ctrl+A
            self.cursor_pos = 0

        elif key == curses.KEY_END or key == 5:  # End or Ctrl+E
            self.cursor_pos = len(self.input_buffer)

        elif key == 21:  # Ctrl+U - clear input
            self.input_buffer = ""
            self.cursor_pos = 0

        elif 32 <= key <= 126:  # Printable characters
            # Insert character at cursor position
            char = chr(key)
            self.input_buffer = (self.input_buffer[:self.cursor_pos] +
                                 char + self.input_buffer[self.cursor_pos:])
            self.cursor_pos += 1

        # Ensure cursor stays within bounds
        self.cursor_pos = max(0, min(self.cursor_pos, len(self.input_buffer)))

        return True

    @staticmethod
    def _validate_steam_path(path: Path) -> bool:
        """Validate if the given path is a valid Steam installation directory"""
        try:
            if not path.exists() or not path.is_dir():
                return False

            # Check for common Steam directory indicators
            steam_indicators = [
                "steamapps",
                "appcache",
                "steam.exe" if platform.system() == "Windows" else "steam",
                "config"
            ]

            path_contents = [item.name.lower() for item in path.iterdir()]

            # At least steamapps should exist for a valid Steam installation
            if "steamapps" not in path_contents:
                return False

            # Check for at least 2 other indicators
            found_indicators = sum(1 for indicator in steam_indicators if indicator.lower() in path_contents)
            return found_indicators >= 2

        except (OSError, PermissionError):
            return False

    def _reset_input_buffer(self):
        """Reset input buffer and cursor position"""
        self.input_buffer = ""
        self.cursor_pos = 0
        curses.curs_set(0)  # Hide cursor

    def _toggle_game_by_number(self, num):
        allowed = set(self.model.get_available_games())
        available_games = []

        for idx, (name, _, target_rel, _) in self.model.game_mapping.items():
            if idx in allowed:
                full_target = self.common_path / target_rel
                if full_target.parent.is_dir():
                    available_games.append(idx)

        if 1 <= num <= len(available_games):
            game_id = available_games[num - 1]
            if game_id in self.selected_games:
                self.selected_games.remove(game_id)
            else:
                self.selected_games.add(game_id)

    def _toggle_all_games(self):
        allowed = set(self.model.get_available_games())
        available_games = set()

        for idx, (name, _, target_rel, _) in self.model.game_mapping.items():
            if idx in allowed:
                full_target = self.common_path / target_rel
                if full_target.parent.is_dir():
                    available_games.add(idx)

        if self.selected_games == available_games:
            self.selected_games.clear()
        else:
            self.selected_games = available_games.copy()

    def _extract_icons(self):
        try:
            base_path = Path(__file__).parent
            icons_source = base_path / "icons"
            icons_dest = Path.cwd() / "icons"

            if not icons_source.exists():
                self.notify("❌ Icons folder not found!")
                return

            if icons_dest.exists():
                shutil.rmtree(icons_dest)

            shutil.copytree(icons_source, icons_dest)
            file_count = sum(1 for _ in icons_dest.rglob('*') if _.is_file())
            self.notify(f"✅ Icons extracted! ({file_count} files)")

        except Exception as e:
            self.notify(f"❌ Extract failed: {e}")

    def _apply_icons_threaded(self):
        def apply_worker():
            self._apply_icons()

        thread = threading.Thread(target=apply_worker)
        thread.daemon = True
        thread.start()

    def _apply_icons(self):
        base_path = Path(__file__).parent

        for game_id in self.selected_games:
            name, src_icon, target_rel, appid = self.model.game_mapping[game_id]
            src = base_path / "icons" / f"style{self.model.current_style}" / src_icon
            dest = self.common_path / target_rel

            if not dest.parent.is_dir():
                self.notify(f"⚠️ {name} folder missing. Skipping.")
                continue
            if not src.is_file():
                self.notify(f"⚠️ Icon file missing for {name}. Skipping.")
                continue

            try:
                shutil.copy(src, dest)
                self.notify(f"✅ {name} applied!")

                # Update library cache
                try:
                    img = Image.open(src).convert("RGB")
                    lib_dir = self.common_path / "appcache" / "librarycache" / str(appid)
                    if not lib_dir.is_dir():
                        self.notify(f"⚠️ Library cache folder missing for {name}. Skipping.")
                        continue

                    existing = [
                        fn for fn in lib_dir.iterdir()
                        if fn.suffix.lower() in (".jpg", ".jpeg")
                    ]
                    if not existing:
                        self.notify(f"⚠️ No existing library icon for {name}. Skipping.")
                        continue

                    hashed_file = existing[0]
                    jpg_dest = lib_dir / hashed_file.name
                    img.save(jpg_dest, "JPEG")
                    self.notify(f"✅ {name} library icon applied!")

                except Exception as e:
                    self.notify(f"❌ Failed library icon for {name}: {e}")

                # Update desktop shortcuts
                try:
                    self._update_desktop_shortcuts(name, appid, dest)
                except Exception as e:
                    self.notify(f"❌ Failed desktop shortcuts for {name}: {e}")

            except Exception as e:
                self.notify(f"❌ Failed {name}: {e}")

    def _update_desktop_shortcuts(self, game_name: str, appid: int, icon_path: Path):
        """Update desktop shortcuts for the given Steam game"""
        import os

        # Get desktop path based on platform
        if platform.system() == "Windows":
            desktop_path = Path.home() / "Desktop"
            public_desktop = Path(os.environ.get('PUBLIC', '')) / "Desktop"
            desktop_paths = [desktop_path, public_desktop] if public_desktop.exists() else [desktop_path]
            shortcut_extensions = ['.url']
        else:  # Linux/macOS
            desktop_path = Path.home() / "Desktop"
            desktop_paths = [desktop_path]
            shortcut_extensions = ['.desktop']

        steam_url_patterns = [
            f"steam://rungameid/{appid}",
            f"steam://run/{appid}",
            f"\"steam://rungameid/{appid}\"",
            f"\"steam://run/{appid}\""
        ]

        shortcuts_updated = 0

        for desktop_dir in desktop_paths:
            if not desktop_dir.exists():
                continue

            for shortcut_file in desktop_dir.iterdir():
                if not shortcut_file.is_file() or shortcut_file.suffix.lower() not in shortcut_extensions:
                    continue

                try:
                    if platform.system() == "Windows":
                        shortcuts_updated += self._update_windows_shortcut(shortcut_file, steam_url_patterns, icon_path)
                    else:
                        shortcuts_updated += self._update_linux_shortcut(shortcut_file, steam_url_patterns, icon_path)
                except:
                    continue

        if shortcuts_updated > 0:
            self.notify(f"✅ {game_name}: Updated {shortcuts_updated} desktop shortcut(s)!")

    @staticmethod
    def _update_windows_shortcut(shortcut_file: Path, steam_patterns: list, icon_path: Path) -> int:
        """Update Windows .url shortcut"""
        try:
            content = shortcut_file.read_text(encoding='utf-8', errors='ignore')

            if any(pattern in content for pattern in steam_patterns):
                lines = content.split('\n')
                icon_line_found = False

                for i, line in enumerate(lines):
                    if line.startswith('IconFile='):
                        lines[i] = f'IconFile={icon_path}'
                        icon_line_found = True
                        break

                if not icon_line_found:
                    for i, line in enumerate(lines):
                        if line.startswith('URL='):
                            lines.insert(i + 1, f'IconFile={icon_path}')
                            lines.insert(i + 2, 'IconIndex=0')
                            break

                shortcut_file.write_text('\n'.join(lines), encoding='utf-8')
                return 1
        except:
            pass

        return 0

    @staticmethod
    def _update_linux_shortcut(shortcut_file: Path, steam_patterns: list, icon_path: Path) -> int:
        """Update Linux .desktop shortcut"""
        try:
            content = shortcut_file.read_text(encoding='utf-8', errors='ignore')

            if any(pattern in content for pattern in steam_patterns):
                lines = content.split('\n')
                icon_line_found = False

                for i, line in enumerate(lines):
                    if line.startswith('Icon='):
                        lines[i] = f'Icon={icon_path}'
                        icon_line_found = True
                        break

                if not icon_line_found:
                    for i, line in enumerate(lines):
                        if line.strip() == '[Desktop Entry]':
                            insert_pos = i + 1
                            while insert_pos < len(lines) and not lines[insert_pos].startswith('['):
                                if lines[insert_pos].startswith('Exec='):
                                    insert_pos += 1
                                    break
                                insert_pos += 1
                            lines.insert(insert_pos, f'Icon={icon_path}')
                            break

                shortcut_file.write_text('\n'.join(lines), encoding='utf-8')
                return 1
        except:
            pass

        return 0

    def notify(self, message: str, timeout: float = 3.0):
        """Add a notification message"""
        with self.notification_lock:
            self.notifications.append((message, time.time() + timeout))


class IconInstallerModel:
    def __init__(self):
        self.current_style = 1
        self.styles = config.STYLES
        self.game_mapping = config.GAME_MAPPING

    def get_available_games(self):
        return [k for k in self.game_mapping
                if not (self.current_style == 1 and k in [6, 7])]


if __name__ == "__main__":
    app = CursesApp()
    app.run()