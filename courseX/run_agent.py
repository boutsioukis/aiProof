#!/usr/bin/env python3
"""
Simple runner script for the courseX course.

This script runs the autonomous agent for this specific course.
You can also use the CLI directly: `ai-student courseX`
"""

import sys
from pathlib import Path

import anyio

from aiStudent import run_autonomous_agent

if __name__ == "__main__":
    # Get the courseX directory (parent of this script)
    course_path = Path(__file__).parent.resolve()
    anyio.run(run_autonomous_agent, course_path)

