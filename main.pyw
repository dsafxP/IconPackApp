import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Set, Tuple, Union, cast

from PIL import Image, ImageTk

import config
from core import IconApplier, IconExtractor, IconInstallerModel, PathManager


class IconPackInstaller:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(config.TITLE)
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Model and state
        self.model = IconInstallerModel()
        self.common_path = PathManager.get_default_steam_path()
        self.selected_games: Set[int] = set()
        self.action_choice = tk.StringVar(value="install")
        self.style_choice = tk.IntVar(value=1)
        self.path_var = tk.StringVar(value=str(self.common_path))

        # Initialize instance attributes
        self.full_banner: ImageTk.PhotoImage | None = None
        self.min_banner: ImageTk.PhotoImage | None = None
        self.path_entry: ttk.Entry | None = None
        self.game_vars: Dict[int, tk.BooleanVar] = {}
        self.current_screen: ttk.Frame | None = None

        # Load images
        self.load_images()

        # Create main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Show welcome screen
        self.show_welcome_screen()

    def load_images(self) -> None:
        """Load banner images"""
        try:
            # Load full banner
            banner_path = Path(__file__).parent / "banner.png"
            if banner_path.exists():
                banner_img: Image.Image = Image.open(banner_path)
                banner_img = banner_img.resize((200, 500), Image.Resampling.LANCZOS)
                self.full_banner = ImageTk.PhotoImage(banner_img)
            else:
                self.full_banner = None

            # Load minimal banner
            min_banner_path = Path(__file__).parent / "min_banner.png"
            if min_banner_path.exists():
                min_banner_img: Image.Image = Image.open(min_banner_path)
                min_banner_img = min_banner_img.resize((200, 80), Image.Resampling.LANCZOS)
                self.min_banner = ImageTk.PhotoImage(min_banner_img)
            else:
                self.min_banner = None

        except Exception as e:
            print(f"Error loading images: {e}")
            self.full_banner = None
            self.min_banner = None

    def clear_screen(self) -> None:
        """Clear current screen"""
        if self.current_screen:
            self.current_screen.destroy()

    def show_welcome_screen(self) -> None:
        """Show welcome screen with full banner"""
        self.clear_screen()

        self.current_screen = ttk.Frame(self.main_frame)
        self.current_screen.pack(fill="both", expand=True)

        # Create horizontal layout
        content_frame = ttk.Frame(self.current_screen)
        content_frame.pack(fill="both", expand=True)

        # Left side - Banner
        banner_frame = ttk.Frame(content_frame)
        banner_frame.pack(side="left", fill="y", padx=10, pady=10)

        if self.full_banner:
            banner_label = ttk.Label(banner_frame, image=cast(Any, self.full_banner))
            banner_label.pack()
        else:
            # Fallback colored frame
            fallback_banner = tk.Frame(banner_frame, width=200, height=500, bg="#1e2328")
            fallback_banner.pack_propagate(False)
            fallback_banner.pack()
            tk.Label(fallback_banner, text="BANNER", fg="white", bg="#1e2328",
                     font=("Arial", 12, "bold")).pack(expand=True)

        # Right side - Content
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=20, pady=10)

        # Title
        title_label = ttk.Label(right_frame, text=f"Welcome to {config.TITLE}",
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ttk.Label(right_frame, text="What do you wish to do?")
        subtitle_label.pack(pady=(0, 20))

        # Action selection
        install_radio = ttk.Radiobutton(right_frame, text="Install Icons",
                                        variable=self.action_choice, value="install")
        install_radio.pack(anchor="w", pady=5)

        # Extract option (greyed out if not PyInstaller bundle)
        extract_state = "normal" if getattr(sys, 'frozen', False) else "disabled"

        extract_radio = ttk.Radiobutton(right_frame, text="Extract Icons",
                                        variable=self.action_choice, value="extract",
                                        state=extract_state)
        extract_radio.pack(anchor="w", pady=5)

        # Spacer
        ttk.Frame(right_frame).pack(fill="both", expand=True)

        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill="x")

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side="right", padx=(10, 0))

        next_btn = ttk.Button(button_frame, text="Next >", command=self.on_welcome_next)
        next_btn.pack(side="right")
        next_btn.focus_set()

    def show_style_screen(self) -> None:
        """Show style selection screen with minimal banner and icon previews"""
        self.clear_screen()

        self.current_screen = ttk.Frame(self.main_frame)
        self.current_screen.pack(fill="both", expand=True)

        # Create layout with minimal banner
        header_frame = ttk.Frame(self.current_screen)
        header_frame.pack(fill="x", padx=10, pady=10)

        # Minimal banner
        if self.min_banner:
            banner_label = ttk.Label(header_frame, image=cast(Any, self.min_banner))
            banner_label.pack(side="left", padx=(0, 20))
        else:
            # Fallback
            fallback_banner = tk.Frame(header_frame, width=200, height=80, bg="#1e2328")
            fallback_banner.pack_propagate(False)
            fallback_banner.pack(side="left", padx=(0, 20))

        # Title area
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side="left", fill="both", expand=True)

        title_label = ttk.Label(title_frame, text="Select an style",
                                font=("Arial", 16, "bold"))
        title_label.pack(anchor="w")

        subtitle_label = ttk.Label(title_frame, text="Choose the icon style you prefer")
        subtitle_label.pack(anchor="w", pady=(5, 0))

        # Content area with scrolling capability
        content_frame = ttk.Frame(self.current_screen)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create scrollable frame for styles
        canvas = tk.Canvas(content_frame)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Style selection with descriptions and previews
        for idx in range(1, len(self.model.styles) + 1):
            style_name, style_desc = self.model.get_style_info(idx)

            # Create frame for this style option
            style_frame = ttk.Frame(scrollable_frame)
            style_frame.pack(fill="x", pady=10, padx=5)

            # Format the display text with description if available
            if style_desc:
                display_text = f"{style_name}  - {style_desc}"
            else:
                display_text = style_name

            style_radio = ttk.Radiobutton(style_frame, text=display_text,
                                        variable=self.style_choice, value=idx)
            style_radio.pack(anchor="w")

            # Load and display preview icons
            preview_frame = ttk.Frame(style_frame)
            preview_frame.pack(anchor="w", padx=(20, 0), pady=(5, 0))
            
            self.load_style_preview_icons(preview_frame, idx)

        # Spacer
        ttk.Frame(content_frame).pack(fill="both", expand=True)

        # Buttons
        button_frame = ttk.Frame(self.current_screen)
        button_frame.pack(fill="x", padx=20, pady=10)

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side="right", padx=(10, 0))

        next_btn = ttk.Button(button_frame, text="Next >", command=self.on_style_next)
        next_btn.pack(side="right")
        next_btn.focus_set()

        back_btn = ttk.Button(button_frame, text="< Back", command=self.show_welcome_screen)
        back_btn.pack(side="right")

    def load_style_preview_icons(self, preview_frame: ttk.Frame, style_idx: int) -> None:
        """Load and display preview icons for a given style"""
        try:
            base_path = Path(__file__).parent
            style_dir = base_path / "icons" / f"style{style_idx}"
            
            if not style_dir.exists():
                return
                
            # Get up to 5 games for preview
            preview_games: List[Tuple[str, Path]] = []
            for _, (game_name, _, _) in self.model.game_mapping.items():
                if len(preview_games) >= 5:
                    break
                
                # Find icon files for this game
                icon_files = self.model.find_icon_files(game_name, style_dir)
                if icon_files:
                    # Prefer JPG, then ICO, then any other format
                    preferred_icon = None
                    for icon_file in icon_files:
                        ext = icon_file.suffix.lower()
                        if ext in ('.jpg', '.jpeg'):
                            preferred_icon = icon_file
                            break
                        elif ext == '.ico' and preferred_icon is None:
                            preferred_icon = icon_file
                        elif preferred_icon is None:
                            preferred_icon = icon_file
                    
                    if preferred_icon:
                        preview_games.append((game_name, preferred_icon))
            
            # Display preview icons
            if preview_games:
                for i, (game_name, icon_path) in enumerate(preview_games):
                    try:
                        # Load and resize image
                        img = Image.open(icon_path)
                        # Resize to small preview size
                        img_resized = img.resize((32, 32), Image.Resampling.LANCZOS)

                        photo = ImageTk.PhotoImage(img_resized)
                        
                        # Create label with image
                        icon_label = ttk.Label(preview_frame, image=photo)

                        icon_label.image = photo
                        
                        icon_label.pack(side="left", padx=(0, 5))
                        
                        # Add tooltip with game name
                        self.create_tooltip(icon_label, game_name)
                        
                    except Exception as e:
                        print(f"Error loading preview icon {icon_path}: {e}")
                        continue
            else:
                # No preview icons available
                no_preview_label = ttk.Label(preview_frame, text="(No preview available)", 
                                            font=("Arial", 8), foreground="gray")
                no_preview_label.pack(side="left")
                
        except Exception as e:
            print(f"Error loading style preview for style {style_idx}: {e}")

    def create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                            relief="solid", borderwidth=1, font=("Arial", 8))
            label.pack()
            
            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def show_game_selection_screen(self) -> None:
        """Show game selection screen"""
        self.clear_screen()

        self.current_screen = ttk.Frame(self.main_frame)
        self.current_screen.pack(fill="both", expand=True)

        # Header with minimal banner
        header_frame = ttk.Frame(self.current_screen)
        header_frame.pack(fill="x", padx=10, pady=10)

        if self.min_banner:
            banner_label = ttk.Label(header_frame, image=cast(Any, self.min_banner))
            banner_label.pack(side="left", padx=(0, 20))
        else:
            fallback_banner = tk.Frame(header_frame, width=200, height=80, bg="#1e2328")
            fallback_banner.pack_propagate(False)
            fallback_banner.pack(side="left", padx=(0, 20))

        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side="left", fill="both", expand=True)

        title_label = ttk.Label(title_frame, text="Select games to install",
                                font=("Arial", 16, "bold"))
        title_label.pack(anchor="w")

        subtitle_label = ttk.Label(title_frame, text="Choose your destination and games")
        subtitle_label.pack(anchor="w", pady=(5, 0))

        # Content area
        content_frame = ttk.Frame(self.current_screen)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Destination folder
        dest_label = ttk.Label(content_frame, text="Destination Folder:", font=("Arial", 10, "bold"))
        dest_label.pack(anchor="w", pady=(0, 5))

        path_frame = ttk.Frame(content_frame)
        path_frame.pack(fill="x", pady=(0, 15))

        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        self.path_entry.pack(side="left", fill="x", expand=True)

        browse_btn = ttk.Button(path_frame, text="Browse...", command=self.browse_folder)
        browse_btn.pack(side="right", padx=(10, 0))

        # Games selection
        games_label = ttk.Label(content_frame, text="Select games:", font=("Arial", 10, "bold"))
        games_label.pack(anchor="w", pady=(0, 5))

        # Create scrollable frame for games
        canvas = tk.Canvas(content_frame, height=200)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Populate games
        self.game_vars = {}
        self.refresh_games_list(scrollable_frame)

        # Buttons
        button_frame = ttk.Frame(self.current_screen)
        button_frame.pack(fill="x", padx=20, pady=10)

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side="right", padx=(10, 0))

        install_btn = ttk.Button(button_frame, text="Install", command=self.on_install)
        install_btn.pack(side="right")
        install_btn.focus_set()

        back_btn = ttk.Button(button_frame, text="< Back", command=self.show_style_screen)
        back_btn.pack(side="right")

    def refresh_games_list(self, parent_frame: ttk.Frame) -> None:
        """Refresh the games list based on current path"""
        # Clear existing widgets
        for widget in parent_frame.winfo_children():
            widget.destroy()

        self.game_vars.clear()

        try:
            current_path = Path(self.path_var.get())
            items = PathManager.get_available_games(self.model, current_path)

            if not items:
                no_games_label = ttk.Label(parent_frame, text="No games found in the specified directory")
                no_games_label.pack(pady=20)
                return

            # Add individual games
            for name, idx, _ in items:
                var = tk.BooleanVar(value=True)
                self.game_vars[idx] = var
                cb = ttk.Checkbutton(parent_frame, text=name, variable=var)
                cb.pack(anchor="w", pady=2)

        except Exception as e:
            error_label = ttk.Label(parent_frame, text=f"Error loading games: {e}")
            error_label.pack(pady=20)

    def browse_folder(self) -> None:
        """Browse for Steam folder"""
        folder = filedialog.askdirectory(initialdir=self.path_var.get())
        if folder:
            self.path_var.set(folder)
            self.common_path = Path(folder)
            # Refresh games list
            # Find the scrollable frame and refresh
            if self.current_screen is not None:
                for child in self.current_screen.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Canvas):
                                canvas_children = subchild.winfo_children()
                                if canvas_children and isinstance(canvas_children[0], ttk.Frame):
                                    scrollable_frame = cast(ttk.Frame, canvas_children[0])
                                    self.refresh_games_list(scrollable_frame)
                                    break

    def show_exit_screen(self, message: str = "Installation completed successfully!") -> None:
        """Show exit screen"""
        self.clear_screen()

        self.current_screen = ttk.Frame(self.main_frame)
        self.current_screen.pack(fill="both", expand=True)

        # Create horizontal layout
        content_frame = ttk.Frame(self.current_screen)
        content_frame.pack(fill="both", expand=True)

        # Left side - Banner
        banner_frame = ttk.Frame(content_frame)
        banner_frame.pack(side="left", fill="y", padx=10, pady=10)

        if self.full_banner:
            banner_label = ttk.Label(banner_frame, image=cast(Any, self.full_banner))
            banner_label.pack()
        else:
            fallback_banner = tk.Frame(banner_frame, width=200, height=500, bg="#1e2328")
            fallback_banner.pack_propagate(False)
            fallback_banner.pack()
            tk.Label(fallback_banner, text="BANNER", fg="white", bg="#1e2328",
                     font=("Arial", 12, "bold")).pack(expand=True)

        # Right side - Content
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=20, pady=10)

        # Title
        title_label = ttk.Label(right_frame, text="Installation complete",
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Message
        message_label = ttk.Label(right_frame, text=message, wraplength=300)
        message_label.pack(pady=(0, 20))

        # Credits
        credits_label = ttk.Label(right_frame, text=config.CREDITS)
        credits_label.pack()

        # Spacer
        ttk.Frame(right_frame).pack(fill="both", expand=True)

        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill="x")

        cancel_btn = ttk.Button(button_frame, text="Cancel", state="disabled")
        cancel_btn.pack(side="right", padx=(10, 0))

        finish_btn = ttk.Button(button_frame, text="Finish", command=self.root.quit)
        finish_btn.pack(side="right")
        finish_btn.focus_set()

        back_btn = ttk.Button(button_frame, text="< Back", state="disabled")
        back_btn.pack(side="right")

    def on_welcome_next(self) -> None:
        """Handle welcome screen next button"""
        if self.action_choice.get() == "install":
            self.show_style_screen()
        elif self.action_choice.get() == "extract":
            self.extract_icons()

    def on_style_next(self) -> None:
        """Handle style screen next button"""
        self.model.current_style = self.style_choice.get()
        self.show_game_selection_screen()

    def on_cancel(self) -> None:
        """Handle cancel button - go to exit screen"""
        self.show_exit_screen("Installation cancelled.")

    def on_install(self) -> None:
        """Handle install button"""
        # Get selected games
        selected_games = {idx for idx, var in self.game_vars.items() if var.get()}

        if not selected_games:
            messagebox.showwarning("No Selection", "Please select at least one game to install icons for.")
            return

        # Start installation in background thread
        self.install_icons_threaded(selected_games)

    def extract_icons(self) -> None:
        """Extract icons to current directory"""
        try:
            base_path = Path(__file__).parent
            destination = Path.cwd()

            # Check if destination already exists
            if (destination / "icons").exists():
                result = messagebox.askyesno("Overwrite",
                                             "Icons folder already exists. Overwrite?")
                if not result:
                    return

            success, message, file_count = IconExtractor.extract_icons(base_path, destination)

            if success:
                self.show_exit_screen(f"Icons extracted successfully!\n{file_count} files extracted.")
            else:
                self.show_exit_screen(f"Extraction failed: {message}")

        except Exception as e:
            self.show_exit_screen(f"Extraction failed: {e}")

    def install_icons_threaded(self, selected_games: Set[int]) -> None:
        """Install icons in background thread"""
        # Disable buttons during installation
        self.set_buttons_enabled(False)

        def install_worker() -> None:
            try:
                base_path = Path(__file__).parent
                applier = IconApplier(self.model, base_path, self.common_path)

                results = applier.apply_icons_to_games(selected_games)

                # Count successful installations
                successful_games = set()
                successful_operations = 0

                for game_name, success, message in results:
                    if success:
                        successful_operations += 1
                        if "Applied" in message and "icon(s)" in message:
                            successful_games.add(game_name)

                # Show results on main thread
                if successful_games:
                    final_message = (f"Installation completed successfully!\n"
                                     f"{len(successful_games)} games updated.\n"
                                     f"{successful_operations} total operations completed.")
                else:
                    final_message = ("Installation completed with issues.\n"
                                     "Some games may not have been updated correctly.")

                self.root.after(0, self.show_exit_screen, final_message)

            except Exception as e:
                self.root.after(0, self.show_exit_screen, f"Installation failed: {e}")

        # Start installation thread
        thread = threading.Thread(target=install_worker, daemon=True)
        thread.start()

    def set_buttons_enabled(self, enabled: bool) -> None:
        """Enable/disable all buttons"""

        def update_buttons(widget: Union[tk.Widget, tk.Tk]) -> None:
            if isinstance(widget, ttk.Button):
                widget.configure(state="normal" if enabled else "disabled")
            for child in widget.winfo_children():
                update_buttons(child)

        update_buttons(self.root)

    def run(self) -> None:
        """Run the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = IconPackInstaller()
    app.run()