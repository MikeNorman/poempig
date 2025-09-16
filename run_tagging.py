#!/usr/bin/env python3
"""
Run the poem tagging process.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.tag_all_poems import main

if __name__ == "__main__":
    load_dotenv()
    main()
