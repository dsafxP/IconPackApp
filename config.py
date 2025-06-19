NAME = "⚙️ MY ICON PACK" # Name displayed at the top

CREDITS = "Made with 💚 by dsafxP" # Displayed at the bottom

# Styles can be defined as:
# - Simple string: "Style Name" (no description)
# - Tuple: ("Style Name", "Description text")
STYLES = [
    "Default",
    # …add as many as you like
]

# game_id: (display name, target relative path, steam app id)
# The system will automatically search for files named after the display name
# in the icons directory and match them by extension to target files
GAME_MAPPING = {
    1: ("Half-Life", r"steamapps\common\Half-Life\valve", 70),
}