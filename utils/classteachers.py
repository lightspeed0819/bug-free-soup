import csv
from utils import connect
from utils import logmaster

_log = logmaster.getLogger()

# Connect to MySQL
conn = connect.connect_to_db()
sql = conn.cursor()

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
    sql.execute("SELECT ID, teacher, co_teacher FROM old_class_teachers;")
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

# Randomly assign class teachers to all classes.
#
# @param not_ct -- list of teachers who cannot be assigned as class teachers.
def random_assign_ct(not_ct:list = ['GF', 'KK', 'NI', 'RJ', 'AT', 'RC', 'DKS', 'LT', 'PS', 'RC', 'RJ', 'WXT']):
    try:
        import random
        # List to store assigned class teachers.
        class_teachers = []

        # Fetch all classes.
        sql.execute("SELECT ID FROM classes;")
        classes = sql.fetchall()

        # For each class, assign a random class teacher.
        for ID in classes:
            clss = ID[0]
            sql.execute("SELECT teacher FROM subject_teachers WHERE class = %s;", [clss])
            subject_teachers = sql.fetchall()
            # Stores all the teachers already assigned as class teachers.
            CTs = [i[1] for i in class_teachers]
        
            # Look for available teachers (preferably those without a paired subject).
            available_teachers = [i[0] for i in subject_teachers if i[0] not in CTs and i[0] not in not_ct]

            if not available_teachers:
                _log.error(f"No eligible teachers found for class {clss}.")
            
            else:

                # Randomly select a teacher from the available ones and append to the list.
                ct = random.choice(available_teachers)
                class_teachers.append([clss, ct])
                _log.debug(f"Assigned {ct} as class teacher for class {clss}.")

                # Update the classes table in MySQL.
                sql.execute("UPDATE classes SET teacher = %s WHERE ID = %s;", [ct, clss])
        # Commit the changes.
        conn.commit()
        return True

    # In case an error occurs...
    # If that happens, it has generally been seen that
    # the error does not occur when the function is run again.
    # It is likely due to the random nature of the assignment.
    # So we can add a try-except block to catch the error in the main program 
    # and try executing again (max 3 attempts).
    except Exception as e:
        conn.rollback()
        _log.error(f"Error while randomly assigning class teachers: {e}")
        return False
