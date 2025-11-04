from utils import connect
from utils import logmaster
import csv

_log = logmaster.getLogger()

# Connect to MySQL
sql_conn = connect.connect_to_db()
cursor = sql_conn.cursor()

# Save all the class timetables to a single csv file in a readable format
#
# @param file_path -- Path to the csv file to which the timetable is to be saved 
def class_timetables(file_path):
    _log.info("Writing class timetables to file...")
    # Get a list of all classes
    cursor.execute("SELECT DISTINCT class FROM timetable ORDER BY class;")
    classes = [i[0] for i in cursor.fetchall()]

    with open(file_path, "w") as file:
        writer = csv.writer(file, delimiter=',')

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        # Header and column names
        for cls in classes:
            writer.writerow([f"---Class {cls}---"])
            writer.writerow(["Day", "1", "2", "3", "4", "5", "6", "7", "8"])

            # Get the timetable entries
            cursor.execute("SELECT subject, teacher, period FROM timetable WHERE class = %s;", [cls])

            data = cursor.fetchall()

            # Create empty timetable
            timetable = {day: [""] * 8 for day in days}

            # Fill timetable
            for subject, teacher, period in data:
                day_num = (period - 1) // 8
                period_num = (period - 1) % 8
                day = days[day_num]
                timetable[day][period_num] = f"{subject} ({teacher})"

            for day in days:
                writer.writerow([day] + timetable[day])

            # Add a blank row after every class's timetable
            writer.writerow(["\n"])
    _log.info(f"Class timetables successfully written to {file_path}.")

# Save all the teachers timetables to a single csv file in a readable format
#
# @param file_path -- Path to the csv file to which the timetable is to be saved 
def teachers_timetables(file_path):
    _log.info("Writing teacher timetables to file...")
    # Get all teachers and their subjects
    cursor.execute("SELECT DISTINCT teacher FROM timetable ORDER BY teacher;")
    teachers = cursor.fetchall()

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    with open(file_path, "w", newline="") as tt_file:
        csv_writer = csv.writer(tt_file)

        for teacher_name in teachers:
            teacher_name = teacher_name[0]
            # Header for the teacher
            csv_writer.writerow([f"——— {teacher_name} ———"])
            csv_writer.writerow(["Day", 1, 2, 3, 4, 5, 6, 7, 8])

            # Get the teacher’s timetable entries
            cursor.execute("""
                SELECT class, period
                FROM timetable
                WHERE teacher = %s;
            """, [teacher_name])
            tt_data = cursor.fetchall()

            # Create empty timetable
            timetable = {day: [""] * 8 for day in days}

            # Fill timetable
            for class_name, period_id in tt_data:
                day_index = (period_id - 1) // 8  # 0–5 (Mon–Sat)
                period_num = (period_id - 1) % 8  # 0–7 (Period 1–8)
                day = days[day_index]
                timetable[day][period_num] = class_name  # Just class name now

            # Write rows
            for day in days:
                csv_writer.writerow([day] + timetable[day])

            # Add a blank row after each teacher’s timetable
            csv_writer.writerow([])
          
    _log.info(f"Teachers' timetables successfully written to {file_path}.")
