#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Perform imports after path configuration
from test import *


def run_test_suite():
    """
    Run all test suites for the application and return overall success status.
    """
    # Initialize the test runner for executing test suites
    runner = unittest.TextTestRunner()

    # Run basic tests
    suite1 = unittest.TestSuite()
    suite1.addTest(TestBasic("test_always_pass"))
    result1 = runner.run(suite1)
    if not result1.wasSuccessful():
        return False

    # Run database setup and teardown tests
    suite2 = unittest.TestSuite()
    suite2.addTest(TestDatabaseSetup("test_create_database"))
    suite2.addTest(TestDatabaseSetup("test_delete_database"))
    result2 = runner.run(suite2)
    if not result2.wasSuccessful():
        return False

    return True


if __name__ == "__main__":
    """
    Main entry point for test execution.

    Runs the complete test suite and exits with status code:
    - 0 if all tests pass
    - 1 if any test fails
    """
    success = run_test_suite()
    sys.exit(0 if success else 1)
