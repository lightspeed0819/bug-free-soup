# Om.
#
# A module to update the teachers, subjects and relevant records in database
#
# USAGE:
#
# from dbupdate import update_db
# update_db()
# 
# AUTHOR: Siddhartha Bhat, 4 Aug 2025
#
# NOTES:
# 'grade' refers to the standard. Like 5, 6, 7 or 8.
# 'class' refers to the section and grade. Like 6B, 7D, 9A, 10F.
# 'period' refers to a specific interval of time in the time table.

import mysql.connector
import json
import csv
import logging
from datetime import datetime

CURR_SESSION_LOG = "logs/" + str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S")) + ".log"

logging.basicConfig(
    filename=CURR_SESSION_LOG,
    filemode='a',
    format="%(asctime)s: %(levelname)s: %(filename)s: %(funcName)s: %(message)s",
    level=logging.DEBUG
)

log = logging.getLogger()

sql = None          # MySQL connection handler
sql_conn = None     # MySQL cursor

# Try to connect to the database
def connect_to_db():
    # Open password file
    log.info("Reading database access credentials...")
    try:
        file = open(".json")
        sql_cred = json.load(file)
        file.close()
    except:
        log.error("Couldn't read database access credentials. Terminating.")
        exit(-1)

    try:    # Attempting to connect
        log.info("Establishing connection to databse...")
        sql_conn = mysql.connector.connect(host = sql_cred['host'],
            user = sql_cred['user'],
            passwd = sql_cred['passwd'],
            database = sql_cred['database'])
        log.info("Connected to database.")
        return sql_conn
    except: # failed to connect
        log.error("Failed to connect to database. Terminating.")
        exit(-1)

def initialise_db():
    # Drop tables so they can be freshly updated
    # Note the order is important (FOREIGN KEYS)
    sql.execute("DROP TABLE IF EXISTS periods_per_week;")
    sql.execute("DROP TABLE IF EXISTS class_alloc;")
    sql.execute("DROP TABLE IF EXISTS teachers;")
    sql.execute("DROP TABLE IF EXISTS subjects;")
    log.debug("Dropped all previous tables from database.")

    # Create table `subjects`
    # @column ID        -- A 2 to 3 char ID for a subject, no long names
    # @column name      -- Full name of subject - for the record
    # @column intensity -- "block" or "single" - For subjects that require consecutive periods
    sql.execute("""
        CREATE TABLE subjects (
            ID        VARCHAR(4)              NOT NULL PRIMARY KEY,
            name      VARCHAR(20)             NOT NULL,
            intensity ENUM("block", "single") NOT NULL
        ) Engine = InnoDB;
    """)
    log.debug("Created table subjects.")

    # Create table `teachers`
    # @column ID      -- A 2 to 3 char ID for a teacher, no long names
    # @column name    -- Full name of teacher - for the record
    # @column subject -- Taught sub
    # @column role    -- Some teachers are incharge of CCA, Time Table etc...
    # @column serial  -- To overwork different teachers fairly
    sql.execute("""
        CREATE TABLE teachers (
            ID                  VARCHAR(3)  NOT NULL PRIMARY KEY,
            name                VARCHAR(40) NOT NULL,
            subject             VARCHAR(4)  NOT NULL,
            qualification       ENUM("PRT", "TGT", "PGT", "MISC") NOT NULL,
            role                ENUM("NONE", "TT", "CCA", "EXDEPT") DEFAULT NULL,
            serial              TINYINT     NOT NULL,
            FOREIGN KEY (subject) REFERENCES subjects(ID) ON UPDATE CASCADE ON DELETE RESTRICT
        ) Engine = InnoDB;
    """)
    log.debug("Created table teachers.")

    # Create table `subject_alloc`
    # @column grade    -- Self explanatory
    # @column subject  -- Do I need to?
    # @column per_week -- Number of periods of this subject in a week
    sql.execute("""
        CREATE TABLE periods_per_week (
            grade    TINYINT    NOT NULL PRIMARY KEY,
            subject  VARCHAR(4) NOT NULL,
            per_week TINYINT    DEFAULT NULL,
            FOREIGN KEY (subject) REFERENCES subjects(ID) ON UPDATE CASCADE ON DELETE RESTRICT
        ) Engine = InnoDB;
    """)
    log.debug("Created table periods_per_week.")

    # Create table `class_alloc`
    # To record what teacher teaches what subject
    # @column class     -- Self explanatory
    # @column subject   -- u r dumb.
    # @column teacher   -- hahahaha.
    # @column is_class_teacher -- If this teacher is the class teacher for this class
    sql.execute("""
        CREATE TABLE class_alloc (
            class            VARCHAR(3)  NOT NULL PRIMARY KEY,
            subject          VARCHAR(4)  NOT NULL,
            teacher          VARCHAR(3)  NOT NULL,
            is_class_teacher BOOL        DEFAULT NULL,
            FOREIGN KEY (subject) REFERENCES subjects(ID) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (teacher) REFERENCES teachers(ID) ON UPDATE CASCADE ON DELETE RESTRICT
        ) Engine = InnoDB;
    """)
    log.debug("Created table class_alloc.")

    log.info("Preparing to load data...")
    sql_conn.commit()

# Loads data from a CSV file into a table
# It is assumed that a header is present in the CSV file
#
# @param dataFile -- path to the CSV file
# @param table    -- table into which data is to be loaded
def load_records_from_file(file_path: str, table: str):
    log.debug("Loading data from file %s to table %s...", file_path, table)
    try:
        file = open(file_path)
        reader = csv.reader(file)
    
        # Ignore the header
        next(reader)

        for row in reader:
            # Creates a string having as many `%s` as there are values in the list `row`
            log.debug("INSERT INTO %s VALUES %s;", table, str(tuple(row)))
            sql.execute("INSERT INTO " + table + " VALUES (" + ', '.join(['%s'] * len(row)) + ");", row)

        file.close()
        log.info("Successfully loaded data from file %s to table %s.", file_path, table)
    except:
        log.warning("Failed to load data from file %s to table %s.", file_path, table)

# Main function
# It all began here ...
def update_db():
    log.info("===== Beginning databse update =====")
    global sql_conn             # MySQL connection handler
    global sql                  # MySQL cursor
    sql_conn = connect_to_db()
    sql = sql_conn.cursor()
    
    # Initialise for data update
    initialise_db()

    # Load the records ...
    load_records_from_file("subjects.csv", "subjects")
    load_records_from_file("teachers.csv", "teachers")
    load_records_from_file("subjectalloc.csv", "periods_per_week")

    # A sample entry into class_alloc
    sql.execute('INSERT INTO class_alloc VALUES ("11A", "CHEM", "SWS", FALSE);')

    sql_conn.commit()
    sql.close()
    sql_conn.close()
    log.info("===== Database update completed =====")
