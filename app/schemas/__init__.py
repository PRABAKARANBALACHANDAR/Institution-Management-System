from .announcements import MYSQL_Announcements
from .course import MYSQL_Courses, PG_Courses
from .departments import MYSQL_Departments, PG_Departments
from .enrollment import (
    MYSQL_StudentEnrollment,
    MYSQL_FacultyAssignment,
    MYSQL_LecturerStudentAssignment,
    PG_FactStudentEnrollment,
    PG_FactFacultyAssignment,
)
from .faculty import MYSQL_Faculty, PG_Faculty
from .faculty_attendance import MYSQLFacultyAttendance, PGFacultyAttendance
from .fees import MYSQL_Fees, PG_Fees
from .leave_req import MYSQL_Leave_Req
from .permissions import MYSQL_Permissions
from .queries import MYSQL_Queries
from .salary import MYSQL_Salary, PG_Salary
from .scores import MYSQLStudentScores, PGStudentScores
from .student import MYSQL_Students, PG_Students
from .student_attendance import MYSQLStudentAttendance, PGStudentAttendance
