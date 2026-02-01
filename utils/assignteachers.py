import random
from utils import connect
from utils import logmaster
from utils import classteachers
_log = logmaster.getLogger()

# Connect to MySQL
sql_conn = connect.connect_to_db()
sql = sql_conn.cursor(dictionary=True)

# Assign subject teachers to each class.
def assign_teachers():
    # Ask if class teachers need to be assigned.
    if input("Do you want to assign class teachers? [Y/n]") in "Yy":
        classteachers.class_teacher_prompt()

    # Assign teacher for a specific subject
    #
    # @param sub -- subject for which teacher is being assigned
    def assign(sub):
        # Get a list of eligible teachers.
        eligible = [t for t in teachers if t["subject"] == sub]
        if eligible:
            # Sort the teachers based on load.
            eligible.sort(key = lambda t: t["load"])
            min_load = eligible[0]["load"]
            # Get a list of least loaded teachers for fair overworking...
            least_loaded = [t for t in eligible if t["load"] == min_load]
            # Chose a random teacher from the least loaded ones...
            chosen = random.choice(least_loaded)
            chosen["load"] += 1
            # Add the chosen teacher to the list of subject teachers.
            sql.execute("UPDATE subject_teachers SET teacher = %s WHERE class = %s AND subject = %s;", [chosen["ID"], class_name, sub])
            _log.debug(f"Assigned {chosen['ID']} to {class_name} for {sub}")     # For debugging purposes.
        # Raise error if no eligible teacher found.
        else:
            _log.error(f"No eligible teacher found for {class_name} - {sub}")

    # Get the list of teachers.
    sql.execute("SELECT ID, subject, serial FROM teachers;")
    teachers = sql.fetchall()
    for t in teachers:
        sql.execute("SELECT COUNT(*) FROM subject_teachers WHERE teacher = %s;", [t["ID"]])
        t["load"] = int(sql.fetchall()[0]["COUNT(*)"])
    
    # Get the list of subjects for each class.
    sql.execute("SELECT * FROM subject_teachers WHERE teacher IS NULL;")
    class_subjects = sql.fetchall()

    # Shit gets real here...
    for class_row in class_subjects:
        # Get the class name and the list of subjects.
        class_name = class_row["class"]
        subject = class_row["subject"]

        # Ignore the cases where the subject is empty...
        if subject:
            assign(subject)

    # Close file and MySQL connection.
    sql_conn.commit()
    sql_conn.close()
    
    _log.info("Teacher assignment completed.")
