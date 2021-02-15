import pymysql

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
            course_name VARCHAR(10) NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (course_name, section_name),
            KEY fk_course_idx (course_name),
            CONSTRAINT fk_course FOREIGN KEY (course_name) REFERENCES courses (course_name)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instructors (
	        instructor_name VARCHAR(256) PRIMARY KEY,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instructors_sections (
	        instructor_name VARCHAR(256) NOT NULL,
            section_name VARCHAR(10) NOT NULL,
            PRIMARY KEY (instructor_name, section_name),
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
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

# make the db if it doesn't exist
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
        "VALUES (%s)", (department.department_name))

    for course in department.courses:
        add_course_if_not_exists(department.department_name, course)

        for section in course.sections:
            add_section_if_not_exists(course.course_name, section)

            for instructor in section.instructors:
                add_instructor_if_not_exists(instructor)
                link_instructor_and_section_if_not_linked(instructor, section)

def add_course_if_not_exists(department_name, course):
    cursor.execute("INSERT IGNORE INTO courses(course_name, department_name)"
        "VALUES (%s, %s)", (course.course_name, department_name))

def add_section_if_not_exists(course_name, section):
    cursor.execute("INSERT IGNORE INTO sections(section_name, course_name) "
        "VALUES (%s, %s)", (section.section_name, course_name))


def add_instructor_if_not_exists(instructor):
    cursor.execute("INSERT IGNORE INTO instructors(instructor_name) VALUES "
        "(%s)", (instructor.instructor_name))

def link_instructor_and_section_if_not_linked(instructor, section):
    cursor.execute("INSERT IGNORE INTO instructors_sections(instructor_name, "
        "section_name) VALUES (%s, %s)", (instructor.instructor_name,
        section.section_name))

def save_snapshot(snapshot):
    cursor.execute("INSERT INTO snapshots(total_seats, open_seats, "
        "waitlist_size, holdfile_size, course_name, section_name) VALUES "
        "(%s, %s, %s, %s, %s, %s)", (snapshot.total_seats, snapshot.open_seats,
        snapshot.waitlist_size, snapshot.holdfile_size, snapshot.course_name,
        snapshot.section_name))

def commit():
    conn.commit()
