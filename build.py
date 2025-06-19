import sys

import PyInstaller.__main__ as pyi

# Get first dragged .ico file for icon (if any)
icon_file = next((f for f in sys.argv[1:] if f.lower().endswith('.ico')), None)

# Basic build command
build_args = [
    'main.py',
    '--onefile',
    '--name=IconPackApp',
    '--add-data=icons:icons',
    '--add-data=config.py:.',
    '--add-data=core.py:.',
    '--add-data=styles.css:.',
]

# Add icon if provided
if icon_file:
    build_args.extend(['--icon', icon_file])

# Run build
pyi.run(build_args)