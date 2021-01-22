import pymysql
import requests

def create_db():
    conn = pymysql.connect(host="localhost", user="root", password="")
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS testudo_courses")
    conn.close()

    conn = pymysql.connect(host="localhost", database="testudo_courses",
        user="root", password="")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            department_name VARCHAR(4) PRIMARY KEY,
	        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
	        course_name VARCHAR(10) PRIMARY KEY,
            department_name VARCHAR(4) NOT NULL,
	        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            KEY fk_department_idx (department_name),
            CONSTRAINT fk_department FOREIGN KEY (department_name) REFERENCES departments (department_name)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections (
	        section_name VARCHAR(10) NOT NULL,
	        instructor VARCHAR(256) NOT NULL,
            course_name VARCHAR(10) NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (course_name, section_name),
            KEY fk_course_idx (course_name),
            CONSTRAINT fk_course FOREIGN KEY (course_name) REFERENCES courses (course_name)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
	        id INT AUTO_INCREMENT PRIMARY KEY,
	        total_seats INT NOT NULL,
            open_seats INT NOT NULL,
            waitlist_size INT NOT NULL,
            holdfile_size INT NOT NULL,
            course_name VARCHAR(10) NOT NULL,
            section_name VARCHAR(10) NOT NULL,
	        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            KEY fk_course_section_idx (section_name),
            CONSTRAINT fk_course_section FOREIGN KEY (course_name, section_name) REFERENCES sections (course_name, section_name)
        );
    """)

    conn.commit()
    conn.close()

create_db()

conn = pymysql.connect(host="localhost", database="testudo_courses",
    user="root", password="")
cursor = conn.cursor()


def add_department_if_not_exists(department):
    """
    The entry point from the scraping code into the db for initializing
    departments, courses, and sections.
    """

    cursor.execute("INSERT IGNORE INTO departments(department_name) "
        f"VALUES ('{department.department_name}')")

    for course in department.courses:
        add_course_if_not_exists(department.department_name, course)

        for section in course.sections:
            add_section_if_not_exists(course.course_name, section)

def add_course_if_not_exists(department_name, course):
    cursor.execute("INSERT IGNORE INTO courses(course_name, department_name)"
        f"VALUES ('{course.course_name}', '{department_name}')")

def add_section_if_not_exists(course_name, section):
    cursor.execute("INSERT IGNORE INTO sections(section_name, instructor, "
        f"course_name) VALUES ('{section.section_name}', '{section.instructor}', "
        f"'{course_name}')")

def save_snapshot(snapshot):
    cursor.execute("INSERT INTO snapshots(total_seats, open_seats, "
        f"waitlist_size, holdfile_size, course_name, section_name) VALUES "
        f"({snapshot.total_seats}, {snapshot.open_seats}, "
        f"{snapshot.waitlist_size}, {snapshot.holdfile_size}, "
        f"'{snapshot.course_name}', '{snapshot.section_name}')")

def commit():
    conn.commit()
