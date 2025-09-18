#!/usr/bin/env python3
"""
Quick launcher for the Interactive Test Suite

This is a simple entry point to start testing your own queries.
"""

from interactive_test import InteractiveTestSuite

if __name__ == '__main__':
    print("🚀 Starting Interactive Test Suite...")
    suite = InteractiveTestSuite()
    suite.run_interactive_session()