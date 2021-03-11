import web
web.config.debug=False
db = web.database(dbn='mysql', db='planetterp', user='root', pw='')

def get_professors():
	return db.select('professors')

def get_course(course_name):
	department = course_name[:4]
	course_number = course_name[4:]

	course = db.select('courses', where='department = $department AND course_number = $course_number', vars={'department': department, 'course_number': course_number})

	if len(course) == 1:
		return course[0]

	return None

def get_course_id(course_name):
	department = course_name[:4]
	course_number = course_name[4:]

	course = db.select('courses', where='department = $department AND course_number = $course_number', vars={'department': department, 'course_number': course_number})

	if len(course) == 1:
		return course[0]['id']

	return None

def insert_professor(name, type_):
	return db.insert('professors', name = name, type = type_)

def insert_course(department, course_number):
	return db.insert('courses', department = department, course_number = course_number)

def get_professor_from_name(name):
	try:
		return db.select('professors', where = 'name = $name', vars={'name': name})[0]
	except IndexError:
		return None

def get_professor_id(name):
	a = db.query('SELECT * FROM professors WHERE name="{}"'.format(name))

	if len(a) == 0:
		return None

	return a[0]['id']

def update_course (course_id, name, description, credits):
	db.update('courses', where = 'id = $course_id', title = name, description = description, credits = credits, vars = {'course_id': course_id})

def insert_professor_course(professor_id, course_id, recent_semester):
	db.insert('professor_courses', professor_id = professor_id, course_id = course_id, recent_semester = recent_semester)

def update_professor_course_recent_semester(professor_id, course_id, semester):
	a = db.query('UPDATE professor_courses SET recent_semester=$semester WHERE professor_id = $professor_id AND course_id = $course_id', vars={'professor_id': professor_id, 'course_id': course_id, 'semester': semester})

def insert_section(course_id, semester, section_number, professor_ids, seats, available_seats, waitlist):
	return db.insert('sections', course_id = course_id, semester = semester, section_number = section_number, professor_ids = professor_ids, seats = seats, available_seats = available_seats, waitlist = waitlist)

def insert_section_meeting(section_id, days, start_time, end_time, building, room, type_):
	db.insert('section_meetings', section_id = section_id, days = days, start_time = start_time, end_time = end_time, building = building, room = room, type = type_)

def update_section_seats(section_id, available_seats, waitlist, seats):
	db.update('sections', where='id = $section_id', available_seats = available_seats, waitlist = waitlist, seats = seats, vars={'section_id': section_id})

def get_section_id (course_id, section_number):
	a = db.query('SELECT * FROM sections WHERE course_id = $course_id AND section_number = $section_number;', vars={'course_id': course_id, 'section_number': section_number})

	if len(a) == 0:
		return None

	return a[0]['id']