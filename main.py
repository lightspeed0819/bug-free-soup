from utils import db
from utils import connect
from utils import logmaster
from utils import prettyprint

# =================== TODO ====================
# Important: Assign class teachers w.r.t previous year data
# Important: pair_subject assignment in the same period
#            the 9th grade and 10th grade errors should fix themselves after this
# Feature:   First period is always of class teacher

# Global variables
sql_conn = connect.connect_to_db()
log = logmaster.getLogger()

# I'll take two. Thank you
cursor_read = sql_conn.cursor(buffered=True)
cursor_write = sql_conn.cursor()

# Returns period(ID)
# @param day    -- day Eg: "mon", "tue" ...
# @param period -- period number Eg: 1, 2, 3, 4 ...
def get_period_id(day: str, period: int):
    cursor_read.execute("SELECT ID FROM periods WHERE day = %s AND period = %s", [day, period])
    #log.debug("SELECT ID FROM periods WHERE day = %s AND period = %s", day, period)
    result = cursor_read.fetchall()
    return result[0][0] if result else None

# Returns teachers(ID)
# from `class` and `subject`
def get_teacher(class_name: str, subject: str):
    cursor_read.execute("SELECT teacher FROM subject_teachers WHERE class = %s AND subject = %s;", [class_name, subject])
    result = cursor_read.fetchall()
    return result[0][0] if result else None

# Verifies that the total number of periods in a week for a class
# does not exceed the maximum number of classes possible in a week
def check_subject_grade_assignments(max_val):
    # Get all the grades in school
    cursor_read.execute("SELECT DISTINCT grade FROM periods_per_week;")

    for i in cursor_read.fetchall():
        # The total periods assigned to a grade in a week 
        cursor_read.execute("SELECT SUM(per_week) FROM periods_per_week WHERE grade = %s", [i[0]])
        assigned_classes_per_week = cursor_read.fetchall()[0][0]
        
        if assigned_classes_per_week != max_val: # Inconsistency
            log.warning("Grade %i has offset of %i subjects w.r.t. weekly quota.", i[0], assigned_classes_per_week - max_val)
            return False

    # All OK
    return True

# Gets the class teacher of specified class
def get_class_teacher(class_name: str):
    cursor_read.execute("SELECT teacher FROM classes WHERE ID = %s;", [class_name])
    result = cursor_read.fetchall()
    return result[0][0] if result else None

# Creates the timetable. A single table that stores all the data on it
def init_timetable_template():
    cursor_write.execute("DROP TABLE IF EXISTS timetable;")
    cursor_write.execute("""CREATE TABLE timetable (
            class   VARCHAR(3) NOT NULL,
            subject VARCHAR(4),
            teacher VARCHAR(4),
            period  TINYINT NOT NULL,
            FOREIGN KEY (class)   REFERENCES classes(ID)  ON UPDATE CASCADE ON DELETE NO ACTION,
            FOREIGN KEY (subject) REFERENCES subjects(ID) ON UPDATE CASCADE ON DELETE NO ACTION,
            FOREIGN KEY (teacher) REFERENCES teachers(ID) ON UPDATE CASCADE ON DELETE NO ACTION,
            FOREIGN KEY (period)  REFERENCES periods(ID)  ON UPDATE CASCADE ON DELETE NO ACTION
        ) Engine = InnoDB;
    """)
    log.debug("Created table timetables.")

# Checks if a period is available in both teacher's and class's timetable
# @param period     -- ID of period
# @param class_name -- ID of class 
# @param teacher    -- ID of teacher
def period_available(period: int, class_name: str, teacher: str):
    # Check if class is free
    cursor_read.execute("SELECT COUNT(*) FROM timetable WHERE class = %s AND period = %s;", [class_name, period])
    class_available = not cursor_read.fetchall()[0][0]

    # Check if teacher is free
    cursor_read.execute("SELECT COUNT(*) FROM timetable WHERE teacher = %s AND period = %s;", [teacher, period])
    teacher_available = not cursor_read.fetchall()[0][0]

    if class_available and teacher_available: # If both class and teacher are available
        return True
    else:                                     # Unavailable
        return False

# Gets specified quantity of periods or empty list if it couldn't find a match
# @param quantity     -- The number of periods needed (together in a block)
# @param class_name   -- ID of class
# @param teacher      -- ID of teacher
# @param day          -- The day
# @param search_start -- Starts searching for period(s) from this period onwards
def get_periods(quantity: int, class_name: str, teacher: str, day: str, search_start: int = 2, search_end: int = 8):
    for i in range(search_start, search_end + 1):
        # Pick sequentially as many periods as `quantity`
        periods = [get_period_id(day, i + j) for j in range(quantity)]
        for j in periods:
            # get_period_id() returns None if the period doesn't exist
            # as (i + j) may have overflown to beyond 8, after which periods don't exist
            if (None in periods) or (not period_available(j, class_name, teacher)): # Invalid selection. Unavailable.
                break 
        else: # Valid selection. Available.
            return periods

    # No set of suitable periods found
    return []

# Updates the timetable assignment cache
# This is cache to store important details about previous assignments
# A nested dictionary: list structure arranged classwise. Like
# 
# cache = {
#     "6A": ["value1", "value2"],
#     "6B": ["value3", "value4", "value5"]
# }
# 
# @param cache      -- The cache variable
# @param class_name -- Name of the class
# @param value      -- The value to append/insert
# @param overwrite  -- Whether to overwrite previously existing value for property
#                      Default behaviour is to append to property if exists else create
def update_cache(cache: dict, class_name: str, value, overwrite: bool):
    if class_name not in cache.keys():
        cache[class_name] = []

    if overwrite:
        cache[class_name] = [value]
    else:
        cache[class_name] += [value] if value not in cache[class_name] else []

# Checks if a value is present in the cache for given class_name
# @param cache      -- The cache variable
# @param class_name -- Name of the class
# @param value      -- The value to check for
def check_cache(cache: dict, class_name: str, value):
    if class_name in cache.keys():
        if value in cache[class_name]:
            return True
    else:
        return False

# We create the timetable lah...
def create_timetable():
    # All the classes, subjects and teachers.
    cursor_read.execute("SELECT * FROM subject_teachers;")

    # Days of the week. This order supports even spread of the rarer subjects
    days = ["mon", "wed", "fri", "tue", "thu", "sat"]

    block_period_days = {}              # Cache to store days where block periods have already been assigned
    class_teacher_periods_assigned = {} # Cache to store if class teacher's periods have been assigned

    missing_periods = 0 # The total number of periods that couldn't be assigned

    for (class_name, subject, teacher, pair_subject) in cursor_read.fetchall():
        # The number of periods per week
        cursor_read.execute("SELECT per_week FROM periods_per_week WHERE grade = %s AND subject = %s;", [int(class_name[:-1]), subject])
        remaining_periods = cursor_read.fetchall()[0][0]

        # Whether this subject can be assigned block periods
        cursor_read.execute("SELECT intensity FROM subjects WHERE ID = %s;", [subject])
        subject_intensity = cursor_read.fetchall()[0][0]

        # Get the teacher for this class-subject combination
        teacher = get_teacher(class_name, subject)
        
        is_class_teacher = get_class_teacher(class_name) == teacher

        update_cache(class_teacher_periods_assigned, class_name, True, True)

        # There will be a point deep in the process where there are periods when teacher is not free,
        # but the class is and there are periods when teacher is free, but the class isn't.
        # The program goes into an infinite loop as no periods can be assigned.
        # Herein referred to as the `teacher-class-availability` paradox.
        # A maximum number of attempts is necessary to prevent breaking.
        attempts = 0
        max_attempts = 3

        while remaining_periods > 0 and attempts <= max_attempts:
            # Loop through each day.
            for i in range(len(days)):
                periods = [] # Suitable periods found for this day
                
                # For subjects with single periods or class teacher's periods
                #          . . . . . . . . .        or if class teacher's periods are already assigned
                start_from = 1 if (is_class_teacher or check_cache(class_teacher_periods_assigned, class_name, True)) else 2

                is_block_day = check_cache(block_period_days, class_name, days[i])

                # For block periods, try to find consecutive periods (of size 2)
                # But what happens is that all periods become block periods and there is none of this
                # subject left for about half the week. Look for block periods when the remaining_periods
                # is more than the number of days left in the week where this subject is not assigned.
                if subject_intensity == "block" and remaining_periods > (len(days) - i) and not is_class_teacher and not is_block_day:
                    periods = get_periods(2, class_name, teacher, days[i], start_from)

                # Preferrably, a class teacher should have at least one class every day
                # so override and get a single period even if the subject is a block subject                
                else:
                    periods = get_periods(1, class_name, teacher, days[i], start_from)

                # If any suitable periods were found for this day
                if periods:
                    remaining_periods -= len(periods)

                    if len(periods) > 1:
                        update_cache(block_period_days, class_name, days[i], False) # Update cache

                    # Update `timetable` with obtained values of period ID
                    for period_id in periods:
                        #log.debug("INSERT INTO timetable VALUES (%s, %s, %s, %s);", class_name, subject, teacher, period_id)
                        cursor_write.execute("INSERT INTO timetable VALUES (%s, %s, %s, %s);", [class_name, subject, teacher, period_id])

                # Necessary as remaining_periods may go into negative before the next
                # check in the while loop. Can't go into negative due to double decrements
                # caused by block periods as block periods are avioded when remaining_periods
                # nears low values
                if remaining_periods <= 0:
                    break
            attempts += 1
        
        # If the max_attempt limit was reached, it means the teacher-class-availablity-paradox was encountered
        # There really isn't much I can do...
        if attempts >= max_attempts:
            log.error("Ran out of attempts: Class '%s' subject '%s' taught by '%s'.", class_name, subject, teacher)

        sql_conn.commit()
    
        # A final evaluation of the timetable assignments for this class
        # Just checking if the assigned periods and the total periods in a week match
        cursor_read.execute("SELECT COUNT(*) FROM timetable WHERE class = %s AND subject = %s;", [class_name, subject])
        periods_assigned = cursor_read.fetchall()[0][0]
        cursor_read.execute("SELECT per_week FROM periods_per_week WHERE grade = %s AND subject = %s;", [int(class_name[:-1]), subject])
        max_periods = cursor_read.fetchall()[0][0]
        if periods_assigned != max_periods:
            log.error("Inconsistency in class '%s' subject '%s'. Off by %i.", class_name, subject, periods_assigned - max_periods)
            missing_periods -= periods_assigned - max_periods

        # Update cache
        if is_class_teacher and max_periods == periods_assigned:
            update_cache(class_teacher_periods_assigned, class_name, True, True)
    
    log.info("Totally, %s periods off.", [missing_periods])

def main():
    # Prompt: Update database records?
    if input("Would you like to update the database with newer records? [Y/n] ") in "Yy":
        db.update_db()
        print("Database updated.")
    else:
        print("Not updating the database.")

    # Prompt: Make a new timetable?
    if input("Would you like to make a new timetable? [Y/n] ") in "Yy":
        # Create an empty timetable
        init_timetable_template()
    
        if check_subject_grade_assignments(6 * 8):
            log.info("Subject assignments perfect...")

        create_timetable()
        print("Timetable updated.")
    else:
        print("Not updating the timetable.")
    
    # Prompt: Save timetables to file?
    if input("Would you like to save the timetables to file? [Y/n] ") in "Yy":
        prettyprint.class_timetables("ctt.csv")
        prettyprint.teachers_timetables("ttt.csv")
        print("Timetables saved.")
    else:
        print("Not saving timetables to csv.")

main()
