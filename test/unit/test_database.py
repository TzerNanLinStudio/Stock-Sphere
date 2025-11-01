#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import mysql.connector
from mysql.connector import Error


class TestDatabaseSetup(unittest.TestCase):
    """
    Unit test class for testing database
    """

    def setUp(self):
        """
        Setup executed before each test
        """
        self.connection = mysql.connector.connect(
            host="localhost", user="root", password=""
        )
        self.cursor = self.connection.cursor()

    def tearDown(self):
        """
        Cleanup executed after each test
        """
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

    def test_create_database(self):
        """
        Test database creation
        """
        try:
            # Check if database exists, drop it if it does
            self.cursor.execute("DROP DATABASE IF EXISTS test_database")
            self.connection.commit()

            # Create database
            self.cursor.execute("CREATE DATABASE test_database")
            self.connection.commit()

            # Check if database was created successfully
            self.cursor.execute("SHOW DATABASES LIKE 'test_database'")
            result = self.cursor.fetchone()

            self.assertIsNotNone(result, "Database 'test_database' creation failed")
            self.assertEqual(
                result[0], "test_database", "Created database name does not match"
            )
        except Error as e:
            self.fail(f"Error occurred while creating database: {e}")

    def test_delete_database(self):
        """
        Test database deletion
        """
        try:
            # Check if database exists
            self.cursor.execute("SHOW DATABASES LIKE 'test_database'")
            result = self.cursor.fetchone()

            if result:
                # Delete database
                self.cursor.execute("DROP DATABASE test_database")
                self.connection.commit()

                # Confirm database has been deleted
                self.cursor.execute("SHOW DATABASES LIKE 'test_database'")
                result_after_deletion = self.cursor.fetchone()

                self.assertIsNone(
                    result_after_deletion, "Database 'test_database' deletion failed"
                )
            else:
                self.skipTest(
                    "Database 'test_database' does not exist, no need to delete"
                )
        except Error as e:
            self.fail(f"Error occurred while deleting database: {e}")


if __name__ == "__main__":
    unittest.main()
