# IconPackApp ![GitHub License](https://img.shields.io/github/license/dsafxP/IconPackApp)

A simple TUI app to apply custom game icons ("styles") to your Steam games.

## Getting Started

1. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the app**  
   ```bash
   python main.py
   ```

## Adding a new style

1. **Edit the styles list**  
   In `config.py`, find the `STYLES` list and add your new style name:
   ```python
   STYLES = [
       "Default",
       "MyCoolStyle",   # ← new style name
   ]
   ```
2. **Create the style folder**  
   Inside the `icons/` directory, make a folder named `styleN` where `N` is the 1‑based index of your style in the `STYLES` list.  
   ```
   icons/
   ├── style1/    ← "Default"
   └── style2/    ← "MyCoolStyle"
   ```
3. **Populate with icons**  
   Add your icon files into `icons/styleN/`. The system will automatically match files by name and extension to the target game files.

## Adding a new game

1. **Define the mapping**  
   In `config.py`, locate the `GAME_MAPPING` dictionary and add a new entry:
   ```python
   GAME_MAPPING = {
      1: ("Half-Life", r"steamapps\common\Half-Life\valve", 70),
      2: ("My Game", r"steamapps\common\My Game\bin", 0),
   }
   ```
   - **Key**: Unique game ID
   - **Tuple**:
     1. Display name (shown in the UI)  
     2. Target directory path under your Steam folder
     3. Steam application identifier

2. **Add icon files for each style**  
   For every `styleN` folder you've created, add your new game's icon files. The system will automatically search for files matching the display name and detect the appropriate extension to match target files in the game directory.

   The application will automatically replace Steam library icons with JPG files found in your style directories. Simply include JPG files named after your games in each style folder, and they will be used for the Steam library display.

## Directory structure example

```
.
├── icons/
│   ├── style1/
│   │   ├── Half-Life.ico
│   │   ├── Half-Life.jpg     ← Library icon
│   │   └── My Game.png
│   └── style2/
│       ├── Half-Life.ico
│       ├── Half-Life.jpg     ← Library icon
│       └── My Game.png
├── build.py
├── config.py
├── main.py
├── README.md
└── styles.css
```

## Building

Build the application:
```bash
python build.py
```

**Add an icon** (drag or specify):
```bash
python build.py your-icon.ico
```
