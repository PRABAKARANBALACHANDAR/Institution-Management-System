from .announcements import MYSQL_Announcements
from .course import MYSQL_Courses, PG_Courses
from .departments import MYSQL_Departments, PG_Departments

from .faculty import MYSQL_Faculty, PG_Faculty
from .faculty_attendance import MYSQLFacultyAttendance, PGFacultyAttendance
from .fees import MYSQL_Fees, PG_Fees
from .golden_source import (
    MYSQL_ETL_Watermark,
    MYSQL_Gold_Courses,
    MYSQL_Gold_Departments,
    MYSQL_Gold_Faculty,
    MYSQL_Gold_FacultyAttendance,
    MYSQL_Gold_Fees,
    MYSQL_Gold_Salary,
    MYSQL_Gold_Snapshot_Batch,
    MYSQL_Gold_Snapshot_Courses,
    MYSQL_Gold_Snapshot_Departments,
    MYSQL_Gold_Snapshot_Faculty,
    MYSQL_Gold_Snapshot_FacultyAttendance,
    MYSQL_Gold_Snapshot_Fees,
    MYSQL_Gold_Snapshot_Salary,
    MYSQL_Gold_Snapshot_StudentAttendance,
    MYSQL_Gold_Snapshot_StudentScores,
    MYSQL_Gold_Snapshot_Students,
    MYSQL_Gold_StudentAttendance,
    MYSQL_Gold_StudentScores,
    MYSQL_Gold_Students,
)
from .leave_req import MYSQL_Leave_Req
from .permissions import MYSQL_Permissions
from .queries import MYSQL_Queries
from .salary import MYSQL_Salary, PG_Salary
from .scores import MYSQLStudentScores, PGStudentScores
from .student import MYSQL_Students, PG_Students
from .student_attendance import MYSQLStudentAttendance, PGStudentAttendance
