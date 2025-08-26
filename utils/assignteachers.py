import pandas as pd
import random
from utils import connect

"""
try:    # Attempting to connect
        sql_conn = mysql.connector.connect(host = "localhost",
            user = "root",
            passwd = "Bageera1",
            database = "timetable")
        sql = sql_conn.cursor(dictionary=True)
except mysql.connector.Error as err: # failed to connect
        exit(-1)
"""

sql_conn = connect.connect_to_db()
sql = sql_conn.cursor(dictionary=True)

# Assign subject teachers to each class.
#
# @param category -- Secondary or Senior Secondary classes (sec, sr_sec).
def assign_teachers():
    # Get the qualification of teachers teaching the class.
    #
    # @param cname -- Class name of the type 6A, 7D, etc.
    def get_qualification(cname: str):
        # Extract number.
        num = int("".join(c for c in cname if c.isdigit()))
        if 6 <= num <= 10:
            return "TGT"
        elif 11 <= num <= 12:
            return "PGT"
    
    # Get the list of teachers.
    sql.execute("SELECT ID, subject, qualification, serial FROM teachers;")
    teachers = sql.fetchall()
    # All a key "load" for each teacher for fair overworking.
    for t in teachers:
          t["load"] = 0
    
    # Extract the subjects of each class.
    classes = pd.read_csv("data/subjectdata.csv")

    # List to store assignments
    assignments = []

    # Shit gets real here...
    for _, row in classes.iterrows():
        # Get the qualification required for that class.
        class_name = row["class"]
        quali = get_qualification(class_name)

        for subject in row[1:]:
            # Look for the double subjects like HIN/SKT.
            if '/' in subject:
                parts = [s.strip() for s in subject.split('/')]

                for part in parts:
                    # Get the eligible teachers and sort them by load.
                    eligible = [t for t in teachers if t["subject"] == part and t["qualification"] == quali]
                    # If suitable teacher found...
                    if eligible:
                        eligible.sort(key = lambda t: t["load"])

                        # Get the least loaded teachers and randomly assign to the class
                        min_load = eligible[0]["load"]
                        least_loaded = [t for t in eligible if t["load"] == min_load]
                        chosen = random.choice(least_loaded)
                        chosen["load"] += 1
                        # print(eligible)
                        # print(chosen)

                        # Save changes to assignments
                        assignments.append({
                                "class": class_name,
                                "subject": part,
                                "teacher": chosen["ID"],
                                "period": subject
                            })
                    # If suitable teacher not found...
                    else:
                        print(class_name, subject)
                        print("No eligible teacher found.")
                        exit(-1)
                        
            # For regular subjects, same logic...
            else:
                if subject == "PHE" or subject == "YOGA":
                    quali = "MISC"
                else:
                    pass
                
                eligible = [t for t in teachers if t["subject"] == subject and t["qualification"] == quali]

                if eligible:
                    eligible.sort(key = lambda x: x["load"])
                    min_load = eligible[0]["load"]
                    least_loaded = [t for t in eligible if t["load"] == min_load]
                    chosen = random.choice(least_loaded)
                    chosen["load"] += 1
                    # print(class_name, subject)
                    # print(eligible)
                    # print(chosen)

                    assignments.append({
                                "class": class_name,
                                "subject": subject,
                                "teacher": chosen["ID"],
                                "period": subject
                            })
                else:
                    print(class_name, subject)
                    print("No eligible teacher found.")
                    exit(-1)
    sql_conn.commit()
    sql.close()
    sql_conn.close()
    return assignments

#for i in assign_teachers():  Testing...
#    print(dict(i))

