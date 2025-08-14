from utils import db
from utils import assignteachers

db.update_db()
print(assignteachers.assign_teachers())
