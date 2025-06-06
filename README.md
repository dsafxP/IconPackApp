# IconPackApp

A simple Textual‑based TUI app to apply custom game icons (“styles”) to your Steam games.

## Getting Started

1. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the app**  
   ```bash
   python main.py
   ```

## Adding a New Style

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
   ├── style1/    ← “Default”
   └── style2/    ← “MyCoolStyle”
   ```
3. **Populate with icons**  
   Copy or add your `.ico` files into `icons/styleN/`, matching the filenames used by the app’s game mapping (e.g. `half-life.ico`, `mygame.ico`, etc.).

## Adding a New Game

1. **Define the mapping**  
   In `config.py`, locate the `GAME_MAPPING` dictionary and add a new entry under the appropriate style index:
   ```python
   GAME_MAPPING = {
      1: ("Half‑Life",   "half-life.ico",   r"steamapps\common\Half-Life\valve\game.ico",  70),
      2: ("My Game",     "mygame.ico",      r"steamapps\common\My Game\bin\icon.ico",      0),
   }
   ```
   - **Key**: Unique game ID
   - **Tuple**:
     1. Display name (shown in the UI)  
     2. Source icon filename (must match the file in each `styleN` folder)  
     3. Target relative path under your Steam folder
     4. Steam application identifier

2. **Add icon files for each style**  
   For every `styleN` folder you’ve created, drop in your new game’s `.ico` file named exactly as in the mapping (e.g. `mygame.ico`).

## Directory Structure Example

```
.
├── icons/
│   ├── style1/
│   │   ├── half‑life.ico
│   │   └── mygame.ico
│   └── style2/
│       ├── half‑life.ico
│       └── mygame.ico
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