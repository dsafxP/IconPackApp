import shutil
import platform
from pathlib import Path
from typing import Set, List, Tuple, Dict
import os

import config


class IconInstallerModel:
    def __init__(self):
        self.current_style = 1
        self.styles = config.STYLES
        self.game_mapping = config.GAME_MAPPING

    def get_style_info(self, index: int) -> Tuple[str, str]:
        """Get style name and description for a given index (1-based)"""
        if 1 <= index <= len(self.styles):
            style = self.styles[index - 1]
            if isinstance(style, tuple):
                return style[0], style[1]
            else:
                return style, ""
        return "", ""

    def get_style_name(self, index: int) -> str:
        """Get just the style name for a given index (1-based)"""
        name, _ = self.get_style_info(index)
        return name

    def get_available_games(self):
        return [k for k in self.game_mapping
                if not (self.current_style == 1 and k in [6, 7])]

    @staticmethod
    def find_icon_files(game_name: str, style_dir: Path) -> List[Path]:
        """Find all icon files for a game name in the given style directory"""
        icon_files = []
        for file in style_dir.glob(f"{game_name}.*"):
            if file.is_file():
                icon_files.append(file)
        return icon_files

    @staticmethod
    def find_target_files(target_dir: Path, extensions: Set[str]) -> List[Path]:
        """Find all files in target directory matching any of the given extensions"""
        target_files: List[Path] = []
        for ext in extensions:
            target_files.extend(target_dir.glob(f"*.{ext}"))
        return target_files

    @staticmethod
    def get_matching_pairs(icon_files: List[Path], target_files: List[Path]) -> List[Tuple[Path, Path]]:
        """Match icon files to target files by extension"""
        pairs = []

        # Create a mapping of extensions to target files
        ext_to_targets: Dict[str, List[Path]] = {}
        for target in target_files:
            ext = target.suffix.lower().lstrip('.')
            if ext not in ext_to_targets:
                ext_to_targets[ext] = []
            ext_to_targets[ext].append(target)

        # Match icon files to targets by extension
        for icon_file in icon_files:
            icon_ext = icon_file.suffix.lower().lstrip('.')
            if icon_ext in ext_to_targets and ext_to_targets[icon_ext]:
                # Use the first matching target file
                target = ext_to_targets[icon_ext][0]
                pairs.append((icon_file, target))
                # Remove the used target to avoid duplicates
                ext_to_targets[icon_ext].remove(target)

        return pairs


class IconExtractor:
    @staticmethod
    def extract_icons(base_path: Path, destination_path: Path) -> Tuple[bool, str, int]:
        """
        Extract icons from the base path to destination path
        Returns: (success, message, file_count)
        """
        try:
            icons_source = base_path / "icons"
            icons_dest = destination_path / "icons"

            # Check if source icons folder exists
            if not icons_source.exists():
                return False, "Icons folder not found!", 0

            # Remove existing destination if it exists
            if icons_dest.exists():
                shutil.rmtree(icons_dest)

            # Copy the entire icons folder
            shutil.copytree(icons_source, icons_dest)

            # Count total files extracted
            file_count = sum(1 for _ in icons_dest.rglob('*') if _.is_file())

            return True, f"Icons extracted! ({file_count} files)", file_count

        except Exception as e:
            return False, f"Extract failed: {e}", 0


class IconApplier:
    def __init__(self, model: IconInstallerModel, base_path: Path, common_path: Path):
        self.model = model
        self.base_path = base_path
        self.common_path = common_path

    def apply_icons_to_games(self, selected_games: Set[int]) -> List[Tuple[str, bool, str]]:
        """
        Apply icons to selected games
        Returns: List of (game_name, success, message) tuples
        """
        results = []

        for game_id in selected_games:
            name, target_rel, appid = self.model.game_mapping[game_id]
            target_dir = self.common_path / target_rel
            style_dir = self.base_path / "icons" / f"style{self.model.current_style}"

            if not target_dir.is_dir():
                results.append((name, False, f"{name} folder missing. Skipping."))
                continue

            if not style_dir.is_dir():
                results.append((name, False, "Style folder missing. Skipping."))
                continue

            # Find all icon files for this game
            icon_files = self.model.find_icon_files(name, style_dir)
            if not icon_files:
                results.append((name, False, f"No icon files found for {name}. Skipping."))
                continue

            # Get unique extensions from icon files
            icon_extensions = {f.suffix.lower().lstrip('.') for f in icon_files}

            # Find matching target files
            target_files = self.model.find_target_files(target_dir, icon_extensions)
            if not target_files:
                results.append((name, False, f"No matching target files found for {name}. Skipping."))
                continue

            # Get matching pairs
            matching_pairs = self.model.get_matching_pairs(icon_files, target_files)
            if not matching_pairs:
                results.append((name, False, f"No matching file pairs found for {name}. Skipping."))
                continue

            # Apply all matching icons
            applied_count = 0
            applied_files = {}  # Track which files were successfully applied
            for src, dest in matching_pairs:
                try:
                    shutil.copy(src, dest)
                    applied_count += 1
                    # Store the destination file path by extension
                    ext = dest.suffix.lower().lstrip('.')
                    applied_files[ext] = dest
                except Exception as e:
                    results.append((name, False, f"Failed to copy {src.name} to {dest.name}: {e}"))
                    continue

            if applied_count > 0:
                results.append((name, True, f"{name}: Applied {applied_count} icon(s)!"))

                # Update library cache
                try:
                    lib_result = self._update_library_cache(appid, icon_files)
                    if lib_result:
                        results.append((name, True, f"{name} library icon applied!"))
                except Exception as e:
                    results.append((name, False, f"Failed library icon for {name}: {e}"))

                # Update desktop shortcuts
                try:
                    shortcuts_count = self._update_desktop_shortcuts(appid, applied_files)
                    if shortcuts_count > 0:
                        results.append((name, True, f"{name}: Updated {shortcuts_count} desktop shortcut(s)!"))
                except Exception as e:
                    results.append((name, False, f"Failed desktop shortcuts for {name}: {e}"))

        return results

    def _update_library_cache(self, appid: int, icon_files: List[Path]) -> bool:
        """Update Steam library cache with JPG file only"""
        lib_dir = self.common_path / "appcache" / "librarycache" / str(appid)
        if not lib_dir.is_dir():
            return False

        # Find existing library cache files
        existing = [
            fn for fn in lib_dir.iterdir()
            if fn.suffix.lower() in (".jpg", ".jpeg")
        ]
        if not existing:
            return False

        # Look for a JPG file only
        jpg_icon = None
        for icon_file in icon_files:
            if icon_file.suffix.lower() in ('.jpg', '.jpeg'):
                jpg_icon = icon_file
                break

        if not jpg_icon:
            # No JPG found, skip library cache update silently
            return False

        # Copy the JPG file directly
        try:
            shutil.copy(jpg_icon, lib_dir / existing[0].name)
            return True
        except Exception:
            raise

    def _update_desktop_shortcuts(self, appid: int, applied_files: dict) -> int:
        """Update desktop shortcuts for the given Steam game"""
        # Get desktop path based on platform
        if platform.system() == "Windows":
            desktop_path = Path.home() / "Desktop"
            # Also check public desktop
            public_desktop = Path(os.environ.get('PUBLIC', '')) / "Desktop"
            desktop_paths = [desktop_path, public_desktop] if public_desktop.exists() else [desktop_path]
            shortcut_extensions = ['.url']
            # Use ICO file for Windows shortcuts
            icon_path = applied_files.get('ico')
        else:  # Linux/macOS
            desktop_path = Path.home() / "Desktop"
            desktop_paths = [desktop_path]
            shortcut_extensions = ['.desktop']
            # Use JPG file for Linux shortcuts, fallback to ICO
            icon_path = applied_files.get('jpg') or applied_files.get('ico')

        if not icon_path:
            # No suitable icon file was applied for shortcuts
            return 0

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

            # Scan all potential shortcut files
            for shortcut_file in desktop_dir.iterdir():
                if not shortcut_file.is_file() or shortcut_file.suffix.lower() not in shortcut_extensions:
                    continue

                try:
                    if platform.system() == "Windows":
                        shortcuts_updated += self._update_windows_shortcut(shortcut_file, steam_url_patterns, icon_path)
                    else:
                        shortcuts_updated += self._update_linux_shortcut(shortcut_file, steam_url_patterns, icon_path)
                except:
                    # Continue processing other shortcuts even if one fails
                    continue

        return shortcuts_updated

    @staticmethod
    def _update_windows_shortcut(shortcut_file: Path, steam_patterns: list, icon_path: Path) -> int:
        """Update Windows .url shortcut"""
        try:
            # Handle .url files (simple text format)
            content = shortcut_file.read_text(encoding='utf-8', errors='ignore')

            # Check if this shortcut points to our Steam game
            if any(pattern in content for pattern in steam_patterns):
                lines = content.split('\n')
                icon_line_found = False

                # Update existing IconFile line or add new one
                for i, line in enumerate(lines):
                    if line.startswith('IconFile='):
                        lines[i] = f'IconFile={icon_path}'
                        icon_line_found = True
                        break

                if not icon_line_found:
                    # Add IconFile line after URL line
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

            # Check if this shortcut points to our Steam game
            if any(pattern in content for pattern in steam_patterns):
                lines = content.split('\n')
                icon_line_found = False

                # Update existing Icon line or add new one
                for i, line in enumerate(lines):
                    if line.startswith('Icon='):
                        lines[i] = f'Icon={icon_path}'
                        icon_line_found = True
                        break

                if not icon_line_found:
                    # Add Icon line in the [Desktop Entry] section
                    for i, line in enumerate(lines):
                        if line.strip() == '[Desktop Entry]':
                            # Find a good place to insert the Icon line
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


class PathManager:
    @staticmethod
    def get_default_steam_path() -> Path:
        """Get the default Steam path based on the current platform"""
        if platform.system() == "Windows":
            return Path(r"C:\Program Files (x86)\Steam")
        elif platform.system() == "Linux":
            return Path.home() / ".local" / "share" / "Steam"
        else:
            return Path("")

    @staticmethod
    def get_available_games(model: IconInstallerModel, common_path: Path) -> List[Tuple[str, int, bool]]:
        """Get list of available games that exist in the Steam directory"""
        allowed = set(model.get_available_games())
        items = []
        for idx, (name, target_rel, _) in model.game_mapping.items():
            if idx in allowed:
                full_target = common_path / target_rel
                if full_target.is_dir():
                    items.append((name, idx, False))
        return items