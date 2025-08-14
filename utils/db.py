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

import mysql.connector
import json
import csv
from utils import logmaster

# Try to connect to the database
def connect_to_db():
    # Open password file
    _log.info("Reading database access credentials...")
    try:
        file = open(".json")
        sql_cred = json.load(file)
        file.close()
    except:
        _log.error("Couldn't read database access credentials. Terminating.")
        exit(-1)
    
    # Attempting to connect
    try:
        _log.info("Establishing connection to databse...")
        sql_conn = mysql.connector.connect(host = sql_cred['host'],
            user = sql_cred['user'],
            passwd = sql_cred['passwd'],
            database = sql_cred['database'])
        _log.info("Connected to database.")
        return sql_conn
    except mysql.connector.Error as err: # failed to connect
        _log.error(err)
        exit(-1)

def _initialise_db():
    # Save last year's class teachers into a table
    _sql.execute("DROP TABLE IF EXISTS old_class_teachers;")
    try:
        _sql.execute("CREATE TABLE old_class_teachers AS SELECT * FROM class_teachers;")
        _log.info("Saved old class teachers data.")
    except:
        _log.warning("Couldn't save old class teachers data.")
    _sql_conn.commit()

    # Drop tables so they can be freshly updated
    # Note the order is important (FOREIGN KEYS)
    _sql.execute("DROP TABLE IF EXISTS periods_per_week;")
    _sql.execute("DROP TABLE IF EXISTS subject_teachers;")
    _sql.execute("DROP TABLE IF EXISTS class_teachers;")
    _sql.execute("DROP TABLE IF EXISTS teachers;")
    _sql.execute("DROP TABLE IF EXISTS subjects;")
    _log.debug("Dropped all previous tables from database.")

    # Create table `subjects`
    # @field ID        -- A 2 to 3 char ID for a subject, no long names
    # @field name      -- Full name of subject - for the record
    # @field intensity -- "block" or "single" - For subjects that require consecutive periods
    _sql.execute("""
        CREATE TABLE subjects (
            ID        VARCHAR(4)              NOT NULL PRIMARY KEY,
            name      VARCHAR(20)             NOT NULL,
            intensity ENUM("block", "single") NOT NULL
        ) Engine = InnoDB;
    """)
    _log.debug("Created table subjects.")

    # Create table `teachers`
    # @field ID      -- A 2 to 3 char ID for a teacher, no long names
    # @field name    -- Full name of teacher - for the record
    # @field subject -- Taught sub
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

    # Create table `class_teachers`
    # @field class      -- 6A, 7B etc...
    # @field teacher    -- The class teacher
    # @field co_teacher -- The co-class teacher
    _sql.execute("""
        CREATE TABLE class_teachers (
            class      VARCHAR(3) NOT NULL PRIMARY KEY,
            subject    VARCHAR(4) NOT NULL,
            teacher    VARCHAR(3) UNIQUE,
            co_teacher VARCHAR(3) UNIQUE,
            FOREIGN KEY (teacher) REFERENCES teachers(ID) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (co_teacher) REFERENCES teachers(ID) ON UPDATE CASCADE ON DELETE RESTRICT
        ) Engine = InnoDB;
    """)
    _log.debug("Created table class_teachers.")

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
            pair_subject VARCHAR(4) DEFAULT NULL,
            FOREIGN KEY (subject) REFERENCES subjects(ID) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (teacher) REFERENCES teachers(ID) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (pair_subject) REFERENCES subjects(ID) ON UPDATE CASCADE ON DELETE RESTRICT
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
def _load_records_from_file(file_path: str, table: str):
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
        _log.info("Successfully loaded data from file %s to table %s.", file_path, table)
    except mysql.connector.Error as err:
        _log.warning(err)

def _load_subject_data(file_path: str, table: str):
    _log.debug("Loading data from file %s to table %s...", file_path, table)
    try:
        file = open(file_path)
        reader = csv.reader(file)
    
        # Ignore the header
        next(reader)

        with open(".json") as file:
            db = json.load(file)['database']

        _sql.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = %s AND table_name = %s;", [db, table])
        fields = int(_sql.fetchone()[0])

        for row in reader:
            for value in row[1::]:
                if '/' in value:
                    sub_options = value.split('/')
                    for i in range(len(sub_options)):
                        _log.debug("INSERT INTO %s VALUES %s;", table, str([row[0], sub_options[i], None, sub_options[0] if len(sub_options) == i + 1 else sub_options[i + 1]]))
                        _sql.execute("INSERT INTO " + table + " VALUES (" + ', '.join(['%s'] * fields) + ");", [row[0], sub_options[i], None, sub_options[0] if len(sub_options) == i + 1 else sub_options[i + 1]])
                else:
                    _log.debug("INSERT INTO %s VALUES %s;", table, str([row[0], value] + ([None] * (fields - 2))))
                    _sql.execute("INSERT INTO " + table + " VALUES (" + ', '.join(['%s'] * fields) + ");", [row[0], value] + ([None] * (fields - 2)))

            # Creates a string having as many `%s` as there are values in the list `row`

        file.close()
        _log.info("Successfully loaded data from file %s to table %s.", file_path, table)
    except mysql.connector.Error as err:
        _log.warning(err)


# Main function
# It all began here ...
def update_db():
    _log.info("===== Beginning databse update =====")

    # Initialise for data update
    _initialise_db()

    # Load the records ...
    _load_records_from_file("data/subjects.csv", "subjects")
    _load_records_from_file("data/teachers.csv", "teachers")
    _load_records_from_file("data/periodsperweek.csv", "periods_per_week")
    _load_subject_data("data/subjectdata.csv", "subject_teachers")

    _sql_conn.commit()
    _sql.close()
    _sql_conn.close()
    _log.info("===== Database update completed =====")

_log = logmaster.getLogger() # Logger
_sql_conn = connect_to_db()  # MySQL connection handler -- intended to be public.
_sql = _sql_conn.cursor()     # MySQL cursor
