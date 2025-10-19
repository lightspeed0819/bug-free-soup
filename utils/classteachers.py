import csv
import connect
import logmaster

_log = logmaster.getLogger()

# Connect to MySQL
conn = connect.connect_to_db()
sql = conn.cursor()

# Update old_class_teachers with data from class_teachers.
def update_old_ct():
    sql.execute("DELETE FROM prev_class_teachers;")
    sql.execute("INSERT INTO prev_class_teachers SELECT * FROM classes;")
    conn.commit()
    _log.info("Updated prev_class_teachers.")

# Assign co class teachers based on class teacher data.
def assign_co_ct():
    sql.execute("SELECT ID, teacher FROM classes;")
    ct_data = sql.fetchall()
    _log.info("Fetching data from table classes...")

    # Dictionary to store the co class teachers along with the class.
    # 
    # key   -- class
    # value -- the co class teacher
    co_ct = {}

    _log.debug("Assigning co class teachers...")
    for cls in ct_data:
        section = cls[0][-1].upper()
        grade = cls[0][:-1]

        # Obtain the section for which that section's class teacher will be the co class teacher.
        co_section = ""
        if section == "A":
            co_section = "E"
        else:
            co_section = chr(ord(section) - 1)

        # Save to dictionary co_ct.
        teacher = cls[1]
        co_ct[grade + co_section] = teacher

    # Update the classes table in MySQL.
    _log.info("Updating co class teachers in table classes...")
    for cls in co_ct:
        sql.execute("UPDATE classes SET co_teacher = %s WHERE ID = %s;", [co_ct[cls], cls])
    conn.commit()
    
    _log.info("Co class teachers assigned successfully.")

# Assign class teachers from a CSV file.
#
# @param file_path -- path to the CSV file having the class teacher info
def assign_ct(file_path):
    # Get the class teacher details from a CSV file.
    file = open(file_path, "r")
    classes = csv.reader(file, delimiter=",")
    next(classes)

    # Update the table classes.
    for cls in classes:
        sql.execute("UPDATE classes SET teacher = %s WHERE ID = %s;", [cls[1], cls[0]])
    
    conn.commit()

# Assign class teachers w.r.t previous year's data.
def promote_class_teachers():
    # Get the previous year's class teacher data.
    sql.execute("SELECT ID, teacher, co_teacher FROM prev_class_teachers;")
    data = sql.fetchall()

    updated_data = []

    for cls, teacher, co_teacher in data:
        grade = int(cls[:-1])
        section = cls[-1].upper()
        new_grade = None
        
        # Apply promotion rules...
        if grade == 8:
            new_grade = 6
        elif grade == 10:
            new_grade = 9
        elif grade == 12:
            new_grade = 11
        else:
            new_grade = grade + 1
        
        # Append the updated data to a new list.
        new_class = f"{new_grade}{section}"
        updated_data.append((new_class, teacher, co_teacher))
    
    try:
        # Save the changes to the table classes.
        for new_class, teacher, co_teacher in updated_data:
            sql.execute("""
                UPDATE classes 
                SET teacher = %s, co_teacher = %s 
                WHERE ID = %s;
            """, [teacher, co_teacher, new_class])
        conn.commit()
        _log.info("Class teachers updated in table classes as per previous data.")

    except Exception as e:
        conn.rollback()
        _log.error(f"Error while promoting class teachers: {e}")
