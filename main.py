# Om Ganeshaya Namah.
# HariH Om.

import mysql.connector
import json
import csv

sql = None
sqlConn = None

# Connect to the database
def connectToDB():
    # Open password file
    with open(".json") as file:
        sqlcred = json.load(file)

    # Connect to the database
    sqlConn = mysql.connector.connect(host = sqlcred['host'],
                user = sqlcred['user'],
                passwd = sqlcred['passwd'],
                database = sqlcred['database'])

    if sqlConn.is_connected(): # Return successfully connected connection object
        print("Connected to database.")
        return sqlConn
    else: # failed to connect
        print("Failed to connect to database. Terminating...")
        exit(-1)

"""
Loads data from a CSV file into a table
@param dataFile - path to the CSV file
@param table    - name of table to which data is entered

It is assumed that a header is present in the CSV file
"""
def loadFileDataIntoTable(dataFile, table):
    with open(dataFile) as file:
        reader = csv.reader(file)
    
    # Ignore the header
    next(reader)

    for row in reader:
        # Creates a string having as many `%s` as there are values in the list `row`
        sql.execute("INSERT INTO " + table + " VALUES (" + ', '.join(['%s'] * len(row)) + ");", row)

    sqlConn.commit()

def updateTeachersList(dataFile, table):
    # Create table `teachers` if it doesn't already exist
    sql.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            ID            VARCHAR(3)         NOT NULL PRIMARY KEY,
            name          VARCHAR(40)        NOT NULL,
            subject       VARCHAR(20)        NOT NULL,
            qualification ENUM("PRT", "PGT", "TGT", "MISC") NOT NULL,
            serial        TINYINT            NOT NULL
        );
    """)

    loadFileDataIntoTable(dataFile, table)

def main():
    # There must be a better way of doing this...
    global sqlConn
    global sql
    sqlConn = connectToDB()
    sql = sqlConn.cursor()
    
    updateTeachersList("teacherslist.csv", "teachers")

    sqlConn.close()

main()
