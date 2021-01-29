import requests
from pathlib import Path
from datetime import datetime
import logging

from doltpy.core import Dolt, DoltException

# A note: dolt only implements a subset of the mysql standard, and a small one
# at that. This means that conveniences like "SELECT EXISTS" and
# "ON DUPLICATE KEY UPDATE" are not implemented and we must work around them.

# dolt logs a lot of stuff (especially since we're sort of abusing their sql
# function by executing commands I know have a good chance of erroring) and is
# probably slowing us down.
logging.getLogger("dolt").setLevel(logging.ERROR)
logging.getLogger("doltpy").setLevel(logging.ERROR)

try:
    dolt = Dolt(Path(__file__).parent)
except AssertionError:
    # this is what doltpy throws when the dir isn't a dolt repo, so now we init
    dolt = Dolt.init(Path(__file__).parent)

DB = "testudo_courses_dolt"

def create_db():
    # work around for https://github.com/dolthub/dolt/issues/1275
    res = dolt.sql(f"""
        SELECT count(*)
        FROM information_schema.TABLES
        WHERE (TABLE_NAME = 'departments')
    """, result_format="json")
    res = res["rows"][0]["COUNT(*)"]
    # if one table exists, assume they all do and don't create any
    if res:
        return

    dolt.sql("""
        CREATE TABLE IF NOT EXISTS departments (
            department_name VARCHAR(4) PRIMARY KEY,
	        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)


    dolt.sql("""
        CREATE TABLE IF NOT EXISTS courses (
	        course_name VARCHAR(10) PRIMARY KEY,
            department_name VARCHAR(4) NOT NULL,
	        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            KEY fk_department_idx (department_name),
            CONSTRAINT fk_department FOREIGN KEY (department_name) REFERENCES departments (department_name)
        );
    """)

    dolt.sql("""
        CREATE TABLE IF NOT EXISTS sections (
	        section_name VARCHAR(10) NOT NULL,
            course_name VARCHAR(10) NOT NULL,
            instructor_names TINYTEXT NOT NULL,
            total_seats INT NOT NULL,
            open_seats INT NOT NULL,
            waitlist_size INT NOT NULL,
            holdfile_size INT NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (course_name, section_name),
            KEY fk_course_idx (course_name),
            CONSTRAINT fk_course FOREIGN KEY (course_name) REFERENCES courses (course_name)
        );
    """)

# ensure the db exists
create_db()




def write_department(department):
    """
    The entry point from the scraping code into the db for writing departments,
    courses, and sections.
    """

    # checking for duplicates is expensive, just ignore them if they occur
    try:
        dolt.sql("INSERT INTO departments(department_name) "
            f"VALUES (\"{department.department_name}\")")
    except DoltException as e:
        if not "duplicate primary key" in str(e):
            raise e


    # doltpy doesn't implement batching, so batch manually
    course_batch = []
    section_batch = []

    for course in department.courses:
        write_course_to_batch(department.department_name, course, course_batch)

        for section in course.sections:
            write_section_to_batch(course.course_name, section, section_batch)


    # since we're using batch we don't get told what error occurs, just that one
    # did occur, so ignore all exceptions (unfortunately).
    try:
        dolt.sql(";".join(course_batch), batch=True)
        dolt.sql(";".join(section_batch), batch=True)
    except DoltException:
        pass


def write_course_to_batch(department_name, course, batch):
    query = ("INSERT INTO courses(course_name, department_name) "
        f"VALUES (\"{course.course_name}\", \"{department_name}\")")
    batch.append(query)


def write_section_to_batch(course_name, section, batch):
    query = ("INSERT INTO sections(section_name, course_name, "
        "instructor_names, total_seats, open_seats, waitlist_size, "
        f"holdfile_size) VALUES (\"{section.section_name}\", \"{course_name}\", "
        f"\"{section.instructor_names}\", {section.total_seats}, "
        f"{section.open_seats}, {section.waitlist_size}, "
        f"{section.holdfile_size})")

    batch.append(query)


def commit(time_started):
    time_ended = datetime.now()

    # stage our tables
    dolt.add(["departments", "courses", "sections"])
    dolt.commit(f"add snapshot ({time_ended}).\n\n"
        "Taken over the following time period: "
        f"{time_started} to {time_ended}.", allow_empty=True)
