# Om.
#
# A module to update the teachers, subjects and relevant records in database 
# 
# AUTHORED ON: 4 Aug 2025
#
# NOTES:
# 'grade' refers to the standard. Like 5, 6, 7 or 8.
# 'class' refers to the section and grade. Like 6B, 7D, 9A, 10F.
# 'period' refers to a specific interval of time in the time table.

import csv
import json
import mysql.connector
from utils import logmaster
from utils import assignteachers
from utils import connect
from utils import classteachers

def _initialise_db():
    # Save last year's class teachers into a table
    _sql.execute("DROP TABLE IF EXISTS old_class_teachers;")
    try:
        _sql.execute("CREATE TABLE old_class_teachers AS SELECT * FROM classes;")
        _log.info("Saved old class teachers data.")
    except:
        _log.warning("Couldn't save old class teachers data.")
    _sql_conn.commit()

    # Drop tables so they can be freshly updated
    # Note the order is important (FOREIGN KEYS)
    _sql.execute("DROP TABLE IF EXISTS timetable;")
    _sql.execute("DROP TABLE IF EXISTS periods_per_week;")
    _sql.execute("DROP TABLE IF EXISTS subject_teachers;")
    _sql.execute("DROP TABLE IF EXISTS classes;")
    _sql.execute("DROP TABLE IF EXISTS teachers;")
    _sql.execute("DROP TABLE IF EXISTS subjects;")
    _sql.execute("DROP TABLE IF EXISTS periods;")
    _log.debug("Dropped all previous tables from database.")

    # Create table `subjects`
    # @field ID        -- A 2 to 3 char ID for a subject, no long names
    # @field name      -- Full name of subject - for the record
    # @field intensity -- "block" or "single" - For subjects that require consecutive periods
    _sql.execute("""
        CREATE TABLE subjects (
            ID        VARCHAR(4)              NOT NULL PRIMARY KEY,
            name      VARCHAR(25)             NOT NULL,
            intensity ENUM("block", "single") NOT NULL
        ) Engine = InnoDB;
    """)
    _log.debug("Created table subjects.")

    # Create table `teachers`
    # @field ID      -- A 2 to 3 char ID for a teacher, no long names
    # @field name    -- Full name of teacher - for the record
    # @field subject -- Subject taught by this person
    # @field qualification -- Qualification of teacher Eg. TGT, PGT...
    # @field role    -- Class teacher of what class OR incharge of CCA, Time Table etc...
    # @field serial  -- To overwork different teachers fairly
    _sql.execute("""
        CREATE TABLE teachers (
            ID            VARCHAR(3)  NOT NULL PRIMARY KEY,
            name          VARCHAR(40) NOT NULL,
            subject       VARCHAR(4)  NOT NULL,
            qualification ENUM("PRT", "TGT", "PGT", "MISC") NOT NULL,
            role          VARCHAR(10) DEFAULT NULL,
            serial        TINYINT     NOT NULL,
            FOREIGN KEY (subject) REFERENCES subjects(ID) ON UPDATE CASCADE ON DELETE RESTRICT
        ) Engine = InnoDB;
    """)
    _log.debug("Created table teachers.")

    # Create table `periods`
    # @field ID     -- An ID for the period
    # @field day    -- mon/tue/wed/...
    # @field period -- The period number Eg. 1st period, 2nd period...
    _sql.execute("""
        CREATE TABLE periods (
            ID     TINYINT AUTO_INCREMENT PRIMARY KEY,
            day    ENUM("mon", "tue", "wed", "thu", "fri", "sat") NOT NULL,
            period TINYINT NOT NULL
        ) Engine = InnoDB;
    """)

    # Create table `classes`
    # @field ID         -- 6A, 7B etc...
    # @field teacher    -- The class teacher
    # @field co_teacher -- The co-class teacher
    _sql.execute("""
        CREATE TABLE classes (
            ID         VARCHAR(3) NOT NULL PRIMARY KEY,
            teacher    VARCHAR(3) UNIQUE,
            co_teacher VARCHAR(3) UNIQUE,
            FOREIGN KEY (teacher) REFERENCES teachers(ID) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (co_teacher) REFERENCES teachers(ID) ON UPDATE CASCADE ON DELETE RESTRICT
        ) Engine = InnoDB;
    """)
    _log.debug("Created table classes.")

    # Create table `subject_teachers`
    # @field class        -- 6A, 7B etc...
    # @field subject      -- subject
    # @field teacher      -- the teacher who teaches `subject` for this class
    # @field pair_subject -- The other optional subject that may/may not exist
    #                        This subject will also have another record where it is the `subject`
    #                        and the teacher for this subject for the same class can be found in that record...
    _sql.execute("""
        CREATE TABLE subject_teachers (
            class        VARCHAR(3) NOT NULL,
            subject      VARCHAR(4) NOT NULL,
            teacher      VARCHAR(3) DEFAULT NULL,
            FOREIGN KEY (subject) REFERENCES subjects(ID) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (teacher) REFERENCES teachers(ID) ON UPDATE CASCADE ON DELETE RESTRICT
        ) Engine = InnoDB;
    """)
    _log.debug("Created table subject_teachers.")
    
    # Create table `periods_per_week`
    # @field grade    -- the grade
    # @field subject  -- subject
    # @field per_week -- Number of periods of this subject in a week
    _sql.execute("""
        CREATE TABLE periods_per_week (
            grade    TINYINT    NOT NULL,
            subject  VARCHAR(4) NOT NULL,
            per_week TINYINT    DEFAULT NULL,
            FOREIGN KEY (subject) REFERENCES subjects(ID) ON UPDATE CASCADE ON DELETE RESTRICT
        ) Engine = InnoDB;
    """)
    _log.debug("Created table periods_per_week.")


    _log.info("Preparing to load data...")
    _sql_conn.commit()

# Loads data from a CSV file into a table
# It is assumed that a header is present in the CSV file
#
# @param file_path -- path to the CSV file
# @param table     -- table into which data is to be loaded
def load_records_from_file(file_path: str, table: str):
    _log.debug("Loading data from file %s to table %s...", file_path, table)
    try:
        file = open(file_path)
        reader = csv.reader(file)
    
        # Ignore the header
        next(reader)

        for row in reader:
            for i in range(len(row)):
                if row[i] == "" or row[i] == "NULL":
                    row[i] = None

            # Creates a string having as many `%s` as there are values in the list `row`
            _log.debug("INSERT INTO %s VALUES %s;", table, str(row))
            _sql.execute("INSERT INTO " + table + " VALUES (" + ', '.join(['%s'] * len(row)) + ");", row)

        file.close()

        _log.info("Successfully loaded data from file %s.", file_path)
    except mysql.connector.Error as err:
        _log.warning(err)

def _clarify_optional_subject(class_name: str, subject_options: list, valid_responses: list):
    print(f"Regarding optional subjects for class {class_name},")
    for i in range(len(subject_options)):
        _sql.execute("SELECT name FROM subjects WHERE ID = %s;", [subject_options[i]])
        print(f"[{i + 1}] {_sql.fetchall()[0][0]}")

    while True:
        choice = input(f"choose the suitable subject [{'/'.join([i for i in valid_responses])}]: ")

        if choice in valid_responses:
            print()
            return subject_options[int(choice) - 1]
        else:
            print(f"Invalid input! You have to choose one among [{'/'.join([i for i in valid_responses])}]")

# Loads data from a very specific CSV file having special needs into the table
# containing weekly data of how many periods of a subject are taught in a week
# The CSV file containing data about what subjects are there for every class
# 
# Of course this code is rubbish. I have to come straighten things here.
# 
# It looks something like:
# [6A, ENG, MAT, ...]
# [6B, sub, sub, sub ...]
# ...
#
# It is assumed that a header is present in the CSV file
#
# @param file_path -- path to the CSV file
# @param table     -- table into which data is to be loaded
def _load_subject_data(file_path: str, table: str):
    _log.debug("Loading data from file %s to table %s...", file_path, table)
    try:
        file = open(file_path)
        reader = csv.reader(file)

        # Ignore the header
        next(reader)

        for row in reader:
            _sql.execute("INSERT IGNORE INTO classes VALUES (%s, %s, %s)", [row[0], None, None])
            for subject in row[1::]: # Everything *after* the first value is a subject. Loop through each one
                if '/' in subject:   # For optional subjects...
                    sub_options = subject.split('/') # We'll have two sub_IDs separated
                    subject = _clarify_optional_subject(row[0], sub_options, [str(i) for i in range(1, len(sub_options) + 1)])

                if subject != "":
                    _log.debug("INSERT INTO %s VALUES %s;", table, str([row[0], subject, None]))
                    _sql.execute("INSERT INTO " + table + " VALUES (" + ', '.join(['%s'] * 3) + ");", [row[0], subject, None])

        file.close()
        _log.info("Successfully loaded data from file %s.", file_path)
    except mysql.connector.Error as err:
        _log.warning(err)

# Loads the assignments for subject teachers for every class into the table
# Real complex thing...
def _upload_subject_teacher_data(data: dict, table: str):
    for i in data:
        _sql.execute("UPDATE " + table + " SET " + table + ".teacher = %s WHERE " + table + ".class = %s AND " + table + ".subject = %s;", [i["teacher"], i["class"], i["subject"]])

# Insert into table `periods` all possible periods
def _add_periods(table: str):
    for i in ["mon", "tue", "wed", "thu", "fri", "sat"]:
        for j in range(1, 9):
            _sql.execute("INSERT INTO " + table + " (day, period) VALUES (%s, %s)", [i, j])

# Main function
# It all began here ...
def update_db():
    _log.info("===== Beginning databse update =====")

    # Initialise for data update
    _initialise_db()

    # Load the records ...
    load_records_from_file("data/subjects.csv", "subjects")
    load_records_from_file("data/teachers.csv", "teachers")
    load_records_from_file("data/periodsperweek.csv", "periods_per_week")
    _load_subject_data("data/subjectdata.csv", "subject_teachers")
    _add_periods("periods")
    _sql_conn.commit()

    _upload_subject_teacher_data(assignteachers.assign_teachers(), "subject_teachers")

    _sql_conn.commit()
    _sql.close()
    _sql_conn.close()
    _log.info("===== Database update completed =====")

# Prompt user for class teacher assignment method
def class_teacher_prompt():
    # Prompt: Assign class teachers from file?
    if input("Do you want to assign class teachers from a CSV file? [Y/n] ") in "Yy":
        classteachers.assign_ct(input("Enter the path to the CSV file: "))
        print("Class teachers assigned from file.")

    # Prompt: Promote class teachers from last year?
    elif input("Do you want to promote class teachers from last year? [Y/n] ") in "Yy":
        try:
            classteachers.promote_class_teachers()
            print("Class teachers promoted from last year.")
        except:
            _log.error("Error promoting class teachers from last year.")
            print("Error promoting class teachers from last year.")
            print("Assigning class teachers randomly...")
            classteachers.random_assign_ct()
    else:
        print("Randomly assigning class teachers...")
        for i in range(3):  # Try thrice to assign class teachers
            if classteachers.random_assign_ct():
                break
            else:
                classteachers.random_assign_ct()
        else:
            _log.error("Error assigning class teachers after 3 attempts.")
            print("Error assigning class teachers.")
    try:
        classteachers.assign_co_ct()
    except:
        pass

_log = logmaster.getLogger() # Logger
_sql_conn = connect.connect_to_db()  # MySQL connection handler -- intended to be public.
_sql = _sql_conn.cursor()     # MySQL cursor
