import json
import mysql.connector
from utils import logmaster

_log = logmaster.getLogger()

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
            database = sql_cred['database'],
        )
        _log.info("Connected to database.")
        return sql_conn
    except mysql.connector.Error as err: # failed to connect
        _log.error(err)
        exit(-1)
