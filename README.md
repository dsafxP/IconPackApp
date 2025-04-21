# IconPackApp

A simple Textual‑based TUI app to apply custom game icons (“styles”) to your Steam games.

## Getting Started

1. **Install dependencies**  
   ```bash
   pip install textual
   ```
2. **Run the app**  
   ```bash
   py main.py
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
      1: ("Half‑Life",   "half-life.ico",   r"Half-Life\valve\game.ico"),
      2: ("My Game",     "mygame.ico",      r"My Game\bin\icon.ico"),
   }
   ```
   - **Key**: Unique game ID
   - **Tuple**:
     1. Display name (shown in the UI)  
     2. Source icon filename (must match the file in each `styleN` folder)  
     3. Target relative path under your Steam common folder

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
├── config.py
├── main.py
├── styles.css
└── README.md
```