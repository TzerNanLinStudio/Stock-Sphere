#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest


class TestBasic(unittest.TestCase):
    """
    Unit test class for the basic Python code
    """

    def test_always_pass(self):
        """
        A simple test that always passes.
        """
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
