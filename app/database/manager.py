import mysql.connector
import json


class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(host=host, user=user, password=password)
        self.cursor = self.conn.cursor()
        self.database = database

    def init_database(self):
        """
        Check if the database exists, create it if it doesn't
        """

        self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        self.conn.database = self.database

    def init_tables(self):
        """
        Check if tables exist, create them if they don't
        """

        # Create basic configuration table - stores the basic configuration parameters of the scheduling system
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS shift_config (
                id INT PRIMARY KEY AUTO_INCREMENT,
                shift_year INT NOT NULL,                 # Scheduling year
                shift_month INT NOT NULL,                # Scheduling month
                first_day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL, # First day of week
                emp_fte_num INT NOT NULL,                # Number of full-time employees
                emp_pt_num INT NOT NULL,                 # Number of part-time employees
                design_off_num INT NOT NULL,             # Number of designated days off
                last_submit_day ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL, # Last submission day
                shift_per_day INT NOT NULL,              # Shifts per day
                fte_num_per_shift INT NOT NULL,          # Full-time employees per shift
                pt_num_per_shift INT NOT NULL,           # Part-time employees per shift
                fte_max_shift_per_wk INT NOT NULL,       # Maximum shifts per week for full-time employees
                fte_max_shift_serial INT NOT NULL,       # Maximum consecutive working days for full-time employees
                pt_max_shift_serial INT NOT NULL,        # Maximum consecutive working days for part-time employees
                fte_diff_per_month INT NOT NULL,         # Allowed shift difference per month for full-time employees
                fte_serial_off INT NOT NULL              # Consecutive days off for full-time employees
            )
        """
        )

        # Create employee basic information table - stores basic employee information
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(50) NOT NULL,                      # Employee name
                employee_type ENUM('FTE', 'PT') NOT NULL,       # Employee type: Full-time(FTE) or Part-time(PT)
                salary_type ENUM('MONTHLY', 'DAILY') NOT NULL,  # Salary type: Monthly or Daily
                salary_amount DECIMAL(10,2) NOT NULL,           # Salary amount
                INDEX idx_name (name),                          # Name index, improves query efficiency
                INDEX idx_type (employee_type)                  # Employee type index
            )
        """
        )

        # Create employee designated days off table - records employee's designated days off
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employee_designated_off (
                id INT PRIMARY KEY AUTO_INCREMENT,
                employee_id INT NOT NULL,                                               # Employee ID, related to employees table
                off_date DATE NOT NULL,                                                 # Day off date
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,   # Foreign key constraint
                INDEX idx_employee_date (employee_id, off_date),                        # Composite index
                UNIQUE KEY unique_employee_off_day (employee_id, off_date)              # Ensure one employee has only one record per day
            )
        """
        )

        # Create shop closing days table - records dates when the shop is not operating
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS shop_close_days (
                id INT PRIMARY KEY AUTO_INCREMENT,
                close_date DATE NOT NULL,                   # Shop closing date
                UNIQUE KEY unique_close_date (close_date),  # Ensure date uniqueness
                INDEX idx_close_date (close_date)           # Date index
            )
        """
        )

        # Schedule table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL UNIQUE,                                                                              # Schedule date
                weekday ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,    # Day of week
                status ENUM('Open', 'Closed') NOT NULL,                                                                 # Operating status
                morning_shift JSON,                                                                                     # Morning shift staff
                evening_shift JSON,                                                                                     # Evening shift staff
                chef VARCHAR(50),                                                                                       # Chef
                remarks TEXT,                                                                                           # Remarks
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                                                         # Creation time
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP                              # Update time
            )
        """
        )

    def insert_config(self, data):
        """
        Insert configuration data into database tables

        Args:
            data (dict): Complete shift scheduling configuration data including shift settings, employee information, designated days off, and shop closing days

        Returns:
            bool: True if successful, False if failed
        """

        try:
            # Insert shift configuration
            config = data["shift_config"]
            self.cursor.execute(
                """
                INSERT INTO shift_config (shift_year, shift_month, first_day_of_week, emp_fte_num, emp_pt_num, 
                                        design_off_num, last_submit_day, shift_per_day, fte_num_per_shift, 
                                        pt_num_per_shift, fte_max_shift_per_wk, fte_max_shift_serial, 
                                        pt_max_shift_serial, fte_diff_per_month, fte_serial_off) 
                VALUES (%(shift_year)s, %(shift_month)s, %(first_day_of_week)s, %(emp_fte_num)s, %(emp_pt_num)s, 
                        %(design_off_num)s, %(last_submit_day)s, %(shift_per_day)s, %(fte_num_per_shift)s, 
                        %(pt_num_per_shift)s, %(fte_max_shift_per_wk)s, %(fte_max_shift_serial)s, 
                        %(pt_max_shift_serial)s, %(fte_diff_per_month)s, %(fte_serial_off)s)
            """,
                config,
            )

            # Insert employee data
            employees_data = [
                (
                    emp["name"],
                    emp["employee_type"],
                    emp["salary_type"],
                    emp["salary_amount"],
                )
                for emp in data["employees"]
            ]
            self.cursor.executemany(
                """
                INSERT INTO employees (name, employee_type, salary_type, salary_amount) 
                VALUES (%s, %s, %s, %s)
            """,
                employees_data,
            )

            # Create mapping from employee name to ID
            self.cursor.execute("SELECT id, name FROM employees")
            employee_name_to_id = {
                name: emp_id for emp_id, name in self.cursor.fetchall()
            }

            # Insert employee designated days off
            off_days_data = []
            for emp_off in data["employee_designated_off"]:
                employee_id = employee_name_to_id[emp_off["employee_name"]]
                for off_date in emp_off["off_dates"]:
                    off_days_data.append((employee_id, off_date))
            self.cursor.executemany(
                """
                INSERT INTO employee_designated_off (employee_id, off_date) 
                VALUES (%s, %s)
            """,
                off_days_data,
            )

            # Insert shop closing days
            close_days_data = [(close_date,) for close_date in data["shop_close_days"]]
            self.cursor.executemany(
                """
                INSERT INTO shop_close_days (close_date) 
                VALUES (%s)
            """,
                close_days_data,
            )

            # Commit all changes to the database
            self.conn.commit()

            print(f"Configuration data successfully inserted into database")
            return True

        except mysql.connector.Error as err:
            # Rollback changes if any error occurs
            self.conn.rollback()

            print(f"Insertion failed: {err}")
            return False

    def get_config(self):
        """
        Extract configuration data from database

        Returns:
            dict: Complete shift scheduling configuration data including shift settings, employee information, designated days off, and shop closing days, or None if failed
        """
        try:
            result = {}

            # Get shift configuration from database (most recent record)
            self.cursor.execute("SELECT * FROM shift_config ORDER BY id DESC LIMIT 1")
            config_row = self.cursor.fetchone()

            if config_row:
                # Get column names to create a dictionary with proper field names
                self.cursor.execute("DESCRIBE shift_config")
                config_columns = [col[0] for col in self.cursor.fetchall()]

                # Create configuration dictionary, excluding the id field
                config_dict = dict(zip(config_columns, config_row))
                config_dict.pop(
                    "id", None
                )  # Remove id field as it's not needed in the output

                result["shift_config"] = config_dict

            # Get employee data from database
            self.cursor.execute(
                "SELECT name, employee_type, salary_type, salary_amount FROM employees ORDER BY id"
            )
            employees_rows = self.cursor.fetchall()

            # Format employee data as a list of dictionaries
            result["employees"] = []
            for row in employees_rows:
                employee_dict = {
                    "name": row[0],
                    "employee_type": row[1],
                    "salary_type": row[2],
                    "salary_amount": float(
                        row[3]
                    ),  # Convert Decimal to float for JSON compatibility
                }
                result["employees"].append(employee_dict)

            # Get employee designated days off with employee names
            self.cursor.execute(
                """
                SELECT e.name, edo.off_date 
                FROM employee_designated_off edo
                JOIN employees e ON edo.employee_id = e.id
                ORDER BY e.name, edo.off_date
            """
            )
            off_days_rows = self.cursor.fetchall()

            # Organize days off by employee name
            employee_off_dict = {}
            for name, off_date in off_days_rows:
                if name not in employee_off_dict:
                    employee_off_dict[name] = []
                employee_off_dict[name].append(
                    off_date.strftime("%Y-%m-%d")
                )  # Format date as string

            # Format days off data as a list of dictionaries
            result["employee_designated_off"] = []
            for employee_name, off_dates in employee_off_dict.items():
                result["employee_designated_off"].append(
                    {"employee_name": employee_name, "off_dates": off_dates}
                )

            # Get shop closing days from database
            self.cursor.execute(
                "SELECT close_date FROM shop_close_days ORDER BY close_date"
            )
            close_days_rows = self.cursor.fetchall()

            # Format closing days as a list of date strings
            result["shop_close_days"] = [
                row[0].strftime("%Y-%m-%d") for row in close_days_rows
            ]

            print(f"Configuration data successfully retrieved from database")
            return result

        except mysql.connector.Error as err:
            print(f"Failed to retrieve configuration: {err}")
            return None

    def insert_schedule(self, data):
        """
        Insert or update a single schedule entry in the database

        Args:
            data (dict): Schedule data containing date, weekday, status, morning_shift, evening_shift, chef, and remarks

        Returns:
            bool: True if successful, False if failed
        """

        try:
            # SQL query for inserting or updating schedule data
            # Uses ON DUPLICATE KEY UPDATE to handle cases where the date already exists
            query = """
                INSERT INTO schedules (date, weekday, status, morning_shift, evening_shift, chef, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                weekday = VALUES(weekday),
                status = VALUES(status),
                morning_shift = VALUES(morning_shift),
                evening_shift = VALUES(evening_shift),
                chef = VALUES(chef),
                remarks = VALUES(remarks)
            """

            # Execute the query with parameters from data
            self.cursor.execute(
                query,
                (
                    data["date"],
                    data["weekday"],
                    data["status"],
                    json.dumps(data["morning_shift"]),  # Convert list to JSON string
                    json.dumps(data["evening_shift"]),  # Convert list to JSON string
                    data["chef"],
                    data["remarks"],
                ),
            )

            # Commit the transaction to make changes permanent
            self.conn.commit()

            print(f"Schedule for {data['date']} successfully saved to database")
            return True

        except mysql.connector.Error as err:
            # Rollback the transaction if any error occurs
            self.conn.rollback()

            print(f"Schedule insertion failed: {err}")
            return False

    def get_schedule(self):
        """
        Extract schedule data from database

        Returns:
            list: List of schedule dictionaries containing date, weekday, status, morning_shift, evening_shift, chef, and remarks, or None if failed
        """

        try:
            result = []

            # Get all schedule records from database, ordered by date
            self.cursor.execute(
                """
                SELECT date, weekday, status, morning_shift, evening_shift, chef, remarks 
                FROM schedules 
                ORDER BY date
            """
            )
            schedule_rows = self.cursor.fetchall()

            # Format each schedule record as a dictionary
            for row in schedule_rows:
                schedule_dict = {
                    "date": row[0].strftime("%Y-%m-%d"),  # Format date as string
                    "weekday": row[1],
                    "status": row[2],
                    "morning_shift": (
                        json.loads(row[3]) if row[3] else []
                    ),  # Parse JSON string to list
                    "evening_shift": (
                        json.loads(row[4]) if row[4] else []
                    ),  # Parse JSON string to list
                    "chef": row[5],
                    "remarks": row[6],
                }
                result.append(schedule_dict)

            print(
                f"Schedule data successfully retrieved from database ({len(result)} records)"
            )
            return result

        except mysql.connector.Error as err:
            print(f"Failed to retrieve schedule: {err}")
            return None

    def delete_database(self, db_name):
        """
        Delete a specified database or all non-system databases
        """

        # Get list of all available databases
        self.cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in self.cursor.fetchall()]

        # List of system databases that should never be deleted
        system_dbs = ["information_schema", "mysql", "performance_schema", "sys"]

        if db_name == "":
            # Delete all non-system databases
            for db in databases:
                if db not in system_dbs:
                    try:
                        self.cursor.execute(f"DROP DATABASE {db}")
                        print(f"Database deleted: {db}")
                    except mysql.connector.Error as err:
                        print(f"Error deleting database {db}: {err}")
        elif db_name in databases:
            # Delete the specified database
            try:
                self.cursor.execute(f"DROP DATABASE {db_name}")
                print(f"Database deleted: {db_name}")

                # Reset the connection if the current database was deleted
                if db_name == self.database:
                    self.database = ""
            except mysql.connector.Error as err:
                print(f"Error deleting database {db_name}: {err}")
        else:
            # Database doesn't exist, no action taken
            print(f"Database {db_name} does not exist, no action taken")

    def close(self):
        """
        Close the database connection and cursor
        """

        self.cursor.close()
        self.conn.close()
