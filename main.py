import shutil
import sys
from pathlib import Path
import platform
from typing import Set, Callable, Any
from textual import on, work
from textual.widgets import Header, Button, Static, SelectionList, Input
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Vertical
from textual.screen import Screen, ModalScreen
from textual.reactive import reactive
from PIL import Image
import config


class IconInstallerModel:
    def __init__(self):
        self.current_style = 1
        self.styles = config.STYLES
        self.game_mapping = config.GAME_MAPPING

    def get_available_games(self):
        return [k for k in self.game_mapping
                if not (self.current_style == 1 and k in [6, 7])]


class ConfirmationScreen(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, message: str, callback: Callable[[], None]):
        super().__init__()
        self.message = message
        self.callback = callback

    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog"):
            yield Static(self.message, classes="dialog-message")
            with Grid(classes="dialog-buttons"):
                yield Button("Confirm", variant="success", id="confirm")
                yield Button("Cancel", variant="error", id="cancel")

    @on(Button.Pressed, "#confirm")
    def confirm_action(self):
        self.callback()
        self.dismiss()

    @on(Button.Pressed, "#cancel")
    def cancel_action(self):
        self.dismiss()


class MainScreen(Screen):
    CSS_PATH = "styles.css"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Container(id="main-content"):
                yield Static(config.NAME, classes="title")
                yield Button("Apply Icons", id="apply", variant="primary")
                yield Button("Select Style", id="style", variant="warning")

                # Only show Extract Icons button when running as PyInstaller bundle
                if getattr(sys, 'frozen', False):
                    yield Button("Extract Icons", id="extract", variant="warning")

                yield Button("Exit", id="exit", variant="error")
            yield Static(config.CREDITS, classes="credit")  # Credit text at bottom

    @on(Button.Pressed, "#apply")
    def show_apply_screen(self):
        self.app.push_screen(GameSelectionScreen())

    @on(Button.Pressed, "#style")
    def show_style_screen(self):
        self.app.push_screen(StyleSelectionScreen())

    @on(Button.Pressed, "#extract")
    def extract_icons(self):
        """Extract icons functionality - copies the icons folder to current working directory"""
        try:
            base_path = Path(__file__).parent

            icons_source = base_path / "icons"
            icons_dest = Path.cwd() / "icons"

            # Check if source icons folder exists
            if not icons_source.exists():
                self.app.notify("❌ Icons folder not found!", timeout=3)
                return

            # If destination already exists, ask for confirmation
            if icons_dest.exists():
                message = "Icons folder already exists. Overwrite?"
                self.app.push_screen(
                    ConfirmationScreen(message, lambda: self._do_extract_icons(icons_source, icons_dest)))
            else:
                self._do_extract_icons(icons_source, icons_dest)

        except Exception as e:
            self.app.notify(f"❌ Extract failed: {e}", timeout=3)

    @on(Button.Pressed, "#exit")
    def exit_app(self):
        self.app.exit()

    def _do_extract_icons(self, source: Path, destination: Path):
        """Perform the actual extraction"""
        try:
            # Remove existing destination if it exists
            if destination.exists():
                shutil.rmtree(destination)

            # Copy the entire icons folder
            shutil.copytree(source, destination)

            # Count total files extracted
            file_count = sum(1 for _ in destination.rglob('*') if _.is_file())

            self.app.notify(f"✅ Icons extracted! ({file_count} files)", timeout=3)

        except Exception as e:
            self.app.notify(f"❌ Extract failed: {e}", timeout=3)


class StyleSelectionScreen(Screen):
    CSS_PATH = "styles.css"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="style-container"):
            yield Static("🎨 SELECT STYLE", classes="title")
            with Grid(id="style-grid"):
                # dynamically generate one button per entry in STYLES
                assert isinstance(app, IconPackApp)  # Type narrowing
                for idx, style_name in enumerate(app.model.styles, start=1):
                    yield Button(style_name, id=f"style-{idx}", classes="style-option")
            yield Button("Back", variant="default", id="back")

    @on(Button.Pressed, ".style-option")
    def select_style(self, event: Button.Pressed):
        # parse the index out of the button id
        button_id = event.button.id
        if button_id is not None:
            idx = int(button_id.split("-", 1)[1])

            assert isinstance(app, IconPackApp)  # Type narrowing
            app.model.current_style = idx
            self.app.notify(f"Style changed to {event.button.label}", timeout=2)

    @on(Button.Pressed, "#back")
    def go_back(self):
        self.app.pop_screen()


class GameSelectionScreen(Screen):
    CSS_PATH = "styles.css"
    selected_games: reactive[Set[Any]] = reactive(set)
    path_input: Input
    selection_list: SelectionList

    def __init__(
            self,
            name: str | None = None,
            ide: str | None = None,
            classes: str | None = None,
    ):
        super().__init__(name, ide, classes)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="game-container"):
            yield Static("🎮 SELECT GAMES", classes="title")

            # file-path input + Set button
            yield Static("Steam folder:", classes="label")

            assert isinstance(app, IconPackApp)  # Type narrowing
            self.path_input = Input(value=str(app.common_path), placeholder=
            "Enter Steam folder…")
            yield self.path_input
            yield Button("Set…", id="set-path", variant="primary")

            # then the game list
            allowed = set(app.model.get_available_games())
            items = []
            for idx, (name, _, target_rel, _) in app.model.game_mapping.items():
                if idx in allowed:
                    full_target = app.common_path / target_rel
                    if full_target.parent.is_dir():
                        items.append((name, idx, False))
            self.selection_list = SelectionList(*items, id="game-list")
            yield self.selection_list

            with Grid(id="game-buttons"):
                yield Button("Select All", id="select-all", variant="default")
                yield Button("Apply Selected", id="apply", variant="success")
                yield Button("Back", id="back", variant="default")

    @on(Button.Pressed, "#set-path")
    def set_path(self):
        new_path = self.path_input.value.strip()
        if new_path:

            assert isinstance(app, IconPackApp)  # Type narrowing
            app.common_path = Path(new_path)
        self.app.pop_screen()
        self.app.push_screen(GameSelectionScreen())

    def on_selection_list_selected_changed(self, _) -> None:
        self.selected_games = set(self.selection_list.selected)

    @on(Button.Pressed, "#select-all")
    def select_all_games(self):
        self.selection_list.select_all()
        self.selected_games = set(self.selection_list.selected)

    @on(Button.Pressed, "#apply")
    def confirm_apply(self):
        message = f"Apply icons to {len(self.selected_games)} games?"
        self.app.push_screen(ConfirmationScreen(message, self.apply_icons))  # type: ignore

    @work(thread=True)
    def apply_icons(self):
        base_path = Path(__file__).parent

        assert isinstance(app, IconPackApp)  # Type narrowing

        for game_id in self.selected_games:
            name, src_icon, target_rel, appid = app.model.game_mapping[game_id]
            src = base_path / "icons" / f"style{app.model.current_style}" / src_icon
            dest = app.common_path / target_rel

            if not dest.parent.is_dir():
                self.app.notify(f"⚠️ {name} folder missing. Skipping.", timeout=3)
                continue
            if not src.is_file():
                self.app.notify(f"⚠️ Icon file missing for {name}. Skipping.", timeout=3)
                continue

            try:
                shutil.copy(src, dest)
                self.app.notify(f"✅ {name} applied!", timeout=2)

                try:
                    # open the .ico, convert to RGB JPEG
                    img = Image.open(src).convert("RGB")
                    lib_dir = (
                        app.common_path / "appcache" / "librarycache" / str(appid)
                    )
                    if not lib_dir.is_dir():
                        self.app.notify(f"⚠️ Library cache folder missing for {name}. Skipping.", timeout=3)
                        continue

                    # Steam names the JPG as a hash; find it
                    existing = [
                        fn for fn in lib_dir.iterdir()
                        if fn.suffix.lower() in (".jpg", ".jpeg")
                    ]
                    if not existing:
                        self.app.notify(f"⚠️ No existing library icon for {name}. Skipping.", timeout=3)
                        continue

                    # overwrite the first (and usually only) one
                    hashed_file = existing[0]
                    jpg_dest = lib_dir / hashed_file.name
                    img.save(jpg_dest, "JPEG")

                    self.app.notify(f"✅ {name} library icon applied!", timeout=2)
                except Exception as e:
                    self.app.notify(f"❌ Failed library icon for {name}: {e}", timeout=3)
            except Exception as e:
                self.app.notify(f"❌ Failed {name}: {e}", timeout=3)

    @on(Button.Pressed, "#back")
    def go_back(self):
        self.app.pop_screen()


class IconPackApp(App):
    CSS_PATH = "styles.css"

    def __init__(self):
        super().__init__()
        self.model = IconInstallerModel()
        # default based on platform
        if platform.system() == "Windows":
            self.common_path = Path(r"C:\Program Files (x86)\Steam")
        elif platform.system() == "Linux":
            self.common_path = Path.home() / ".local" / "share" / "Steam"
        else:
            self.common_path = Path("")

    def on_mount(self) -> None:
        self.push_screen(MainScreen())


if __name__ == "__main__":
    app = IconPackApp()
    app.run()