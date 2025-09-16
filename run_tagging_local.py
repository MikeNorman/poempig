#!/usr/bin/env python3
"""
Runner for local poem tagging script.
"""

import sys
import os

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from tag_all_poems_local import main

if __name__ == "__main__":
    main()
