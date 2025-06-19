import sys
from pathlib import Path
from typing import Set, Callable, Any
from textual import on, work
from textual.widgets import Header, Button, Static, SelectionList, Input
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Vertical
from textual.screen import Screen, ModalScreen
from textual.reactive import reactive

import config
from core import IconInstallerModel, IconExtractor, IconApplier, PathManager


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


class WelcomeScreen(Screen):
    """Initial screen asking what the user wants to do"""
    CSS_PATH = "styles.css"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Container(id="main-content"):
                yield Static(config.NAME, classes="title")
                yield Static("What would you like to do?", classes="subtitle")

                yield Button("Install Icons", id="install", variant="success")
                yield Button("Extract Icons", id="extract", variant="primary")
                yield Button("Exit", id="exit", variant="error")

            yield Static(config.CREDITS, classes="credit")

    @on(Button.Pressed, "#extract")
    def extract_icons(self):
        """Extract icons functionality - copies the icons folder to current working directory"""
        try:
            base_path = Path(__file__).parent

            # Check if destination already exists, ask for confirmation
            if (Path.cwd() / "icons").exists():
                message = "Icons folder already exists. Overwrite?"
                self.app.push_screen(
                    ConfirmationScreen(message, lambda: self._do_extract_icons(base_path)))
            else:
                self._do_extract_icons(base_path)

        except Exception as e:
            self.app.notify(f"❌ Extract failed: {e}", timeout=3)

    def _do_extract_icons(self, source_base: Path):
        """Perform the actual extraction and go to exit screen"""
        success, message, file_count = IconExtractor.extract_icons(source_base, Path.cwd())

        if success:
            self.app.notify(f"✅ {message}", timeout=3)
        else:
            self.app.notify(f"❌ {message}", timeout=3)

        # Go to exit screen after extraction
        self.app.push_screen(ExitScreen(f"Extraction {'completed' if success else 'failed'}!"))

    @on(Button.Pressed, "#install")
    def install_icons(self):
        """Go to style selection for icon installation"""
        self.app.push_screen(StyleSelectionScreen())

    @on(Button.Pressed, "#exit")
    def exit_app(self):
        self.app.exit()


class StyleSelectionScreen(Screen):
    """Style selection screen for installation"""
    CSS_PATH = "styles.css"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="style-container"):
            yield Static("🎨 SELECT STYLE", classes="title")
            yield Static("Choose an icon style for installation:", classes="subtitle")

            with Grid(id="style-grid"):
                assert isinstance(app, IconPackApp)  # Type narrowing
                for idx, style_name in enumerate(app.model.styles, start=1):
                    yield Button(style_name, id=f"style-{idx}", classes="style-option")

            # Show Back button if running as bundle, Exit button if not
            if getattr(sys, 'frozen', False):
                yield Button("Back", variant="default", id="back")
            else:
                yield Button("Exit", variant="error", id="exit")

    @on(Button.Pressed, ".style-option")
    def select_style(self, event: Button.Pressed):
        # parse the index out of the button id
        button_id = event.button.id
        if button_id is not None:
            idx = int(button_id.split("-", 1)[1])

            assert isinstance(app, IconPackApp)  # Type narrowing
            app.model.current_style = idx
            self.app.notify(f"Style selected: {event.button.label}", timeout=2)

            # Proceed to game selection
            self.app.push_screen(GameSelectionScreen())

    @on(Button.Pressed, "#back")
    def go_back(self):
        self.app.pop_screen()

    @on(Button.Pressed, "#exit")
    def exit_app(self):
        self.app.exit()


class GameSelectionScreen(Screen):
    """Game selection and installation screen"""
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
            yield Static("Choose games to install icons for:", classes="subtitle")

            # Steam folder path input
            yield Static("Steam folder:", classes="label")
            assert isinstance(app, IconPackApp)  # Type narrowing
            self.path_input = Input(value=str(app.common_path), placeholder="Enter Steam folder path…")
            yield self.path_input
            yield Button("Update Path", id="set-path", variant="primary")

            # Game selection list
            items = PathManager.get_available_games(app.model, app.common_path)
            self.selection_list = SelectionList(*items, id="game-list")
            yield self.selection_list

            with Grid(id="game-buttons"):
                yield Button("Toggle All", id="toggle-all", variant="default")
                yield Button("Install Selected", id="install", variant="success")
                yield Button("Back", id="back", variant="default")

    @on(Button.Pressed, "#set-path")
    def set_path(self):
        new_path = self.path_input.value.strip()
        if new_path:
            assert isinstance(app, IconPackApp)  # Type narrowing
            app.common_path = Path(new_path)
            self.app.notify("Steam path updated", timeout=2)

            # Refresh the game list with new path
            items = PathManager.get_available_games(app.model, app.common_path)
            self.selection_list.clear_options()
            for item in items:
                self.selection_list.add_option(item)

    def on_selection_list_selected_changed(self, _) -> None:
        self.selected_games = set(self.selection_list.selected)

    @on(Button.Pressed, "#toggle-all")
    def toggle_all_games(self):
        if self.selected_games:
            # If any games are selected, deselect all
            self.selection_list.deselect_all()
        else:
            # If no games are selected, select all
            self.selection_list.select_all()
        self.selected_games = set(self.selection_list.selected)

    @on(Button.Pressed, "#install")
    def confirm_install(self):
        if not self.selected_games:
            self.app.notify("⚠️ Please select at least one game", timeout=3)
            return

        message = f"Install icons for {len(self.selected_games)} selected games?"
        self.app.push_screen(ConfirmationScreen(message, self.install_icons))  # type: ignore

    @work(thread=True)
    def install_icons(self):
        assert isinstance(app, IconPackApp)  # Type narrowing

        base_path = Path(__file__).parent
        applier = IconApplier(app.model, base_path, app.common_path)

        # Use call_from_thread to safely call async methods from the worker thread
        self.app.call_from_thread(self.app.notify, "🔄 Installing icons...", timeout=2)
        results = applier.apply_icons_to_games(self.selected_games)

        # Count successful installations
        successful_games = set()
        total_operations = 0
        successful_operations = 0

        for game_name, success, message in results:
            total_operations += 1
            if success:
                successful_operations += 1
                # Extract game name from message if it's a main installation
                if "Applied" in message and "icon(s)" in message:
                    successful_games.add(game_name)
                # Use call_from_thread for notifications from worker thread
                self.app.call_from_thread(self.app.notify, f"✅ {message}", timeout=1)
            else:
                self.app.call_from_thread(self.app.notify, f"⚠️ {message}", timeout=2)

        # Show completion summary and go to exit screen
        if successful_games:
            summary = f"Installation completed!\n{len(successful_games)} games updated successfully."
        else:
            summary = "Installation completed with issues.\nCheck the notifications for details."

        # Use call_from_thread to safely push screen from worker thread
        self.app.call_from_thread(self.app.push_screen, ExitScreen(summary))

    @on(Button.Pressed, "#back")
    def go_back(self):
        self.app.pop_screen()


class ExitScreen(Screen):
    """Final screen showing completion status"""
    CSS_PATH = "styles.css"

    def __init__(self, completion_message: str):
        super().__init__()
        self.completion_message = completion_message

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Container(id="main-content"):
                yield Static("✅ COMPLETE", classes="title")
                yield Static(self.completion_message, classes="completion-message")
                yield Button("Exit", id="exit", variant="primary")

            yield Static(config.CREDITS, classes="credit")

    @on(Button.Pressed, "#exit")
    def exit_app(self):
        self.app.exit()


class IconPackApp(App):
    CSS_PATH = "styles.css"

    def __init__(self):
        super().__init__()
        self.model = IconInstallerModel()
        self.common_path = PathManager.get_default_steam_path()

    def on_mount(self) -> None:
        # Skip welcome screen if NOT running as PyInstaller bundle
        if not getattr(sys, 'frozen', False):
            self.push_screen(StyleSelectionScreen())
        else:
            self.push_screen(WelcomeScreen())


if __name__ == "__main__":
    app = IconPackApp()
    app.run()