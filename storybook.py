#!/usr/bin/env python3
"""
Magic Storybook - Smart Launcher
Auto-detects display and launches appropriate version
"""

import os
import sys
import subprocess

def has_display():
    """Check if a display is available"""
    # Check DISPLAY environment variable
    if 'DISPLAY' in os.environ:
        return True
    
    # Check if running on console
    try:
        result = subprocess.run(
            ['xset', 'q'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1
        )
        return result.returncode == 0
    except:
        return False

def main():
    """Launch appropriate version"""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for display
    if has_display():
        print("🖥️  Display detected - launching touchscreen UI...")
        ui_script = os.path.join(script_dir, 'storybook_ui.py')
        
        if os.path.exists(ui_script):
            # Launch UI version
            os.execv(sys.executable, [sys.executable, ui_script] + sys.argv[1:])
        else:
            print("❌ storybook_ui.py not found!")
            print("   Run the setup script to install UI files.")
            sys.exit(1)
    else:
        print("💻 No display detected - launching console version...")
        console_script = os.path.join(script_dir, 'storybook_console.py')
        
        if os.path.exists(console_script):
            # Launch console version
            os.execv(sys.executable, [sys.executable, console_script] + sys.argv[1:])
        else:
            print("❌ storybook_console.py not found!")
            print("   Run the setup script to install console files.")
            sys.exit(1)

if __name__ == "__main__":
    main()
