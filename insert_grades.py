import csv
import web
import model
import requests
from bs4 import BeautifulSoup

db = web.database(dbn='mysql', db='planetterp', user='root', pw='')

def get_professors(semester):
	professors_courses = {}
	ids = ["left-course-prefix-column", "right-course-prefix-column"]

	for id_ in ids:
		page = requests.get('https://app.testudo.umd.edu/soc/' + semester).text
		soup = BeautifulSoup(page, 'html.parser')

		for dept in soup.find(id=id_).find_all('a'):
			a = dept.text.split("\n")[1]

			page = requests.get('https://app.testudo.umd.edu/soc/' + dept['href']).text

			soup = BeautifulSoup(page, 'html.parser')

			courses = ""

			for course in soup.find_all(class_='course'):
				course_name = course['id']

				courses += course_name + ","
				
			courses = courses[:-1] # Remove end comma

			page = requests.get('https://app.testudo.umd.edu/soc/' + semester + '/sections?courseIds=' + courses).text

			soup = BeautifulSoup(page, 'html.parser')

			for course in soup.find_all(class_='course-sections'):
				course_name = course['id']

				professors_courses[course_name] = {}

				for section in course.select('.delivery-f2f, .delivery-blended, .delivery-online'):
					section_id = -1

					s = section.find_all(class_='section-info-container')[0]
					section_number = s.find(class_='section-id').text.strip()
					professors = s.find_all(class_='section-instructors')[0].text.replace(", ", ",").split(",")
					
					professor_ids = ""

					for professor in professors:
						professor = professor.strip()

						professors_courses[course_name][section_number] = professor
						break
	return professors_courses

def insert_grades(semester):
	professors_courses = get_professors(semester)
	print("On semester " + semester)
	with open(semester + '.csv', 'r') as f:
		reader = csv.DictReader(f)

		for row in reader:
			course = row['Course']
			course_id = model.get_course_id(course)
			section = row['Sect']

			if not course_id:
				print(course + " not in database")
				course_id = model.insert_course(course[:4], course[4:])

			if section.isdigit and len(str(section)) == 3:
				section = "0" + section

			matches = 0
			if not course in professors_courses or not section in professors_courses[course]:
				print("Missing professor for {} {}".format(course, section))
				professor_id = None
			else:
				professor_name = professors_courses[course][section]
				professor = model.get_professor_from_name(professor_name)

				if not professor:
					if professor_name == 'Instructor: TBA':
						professor_id = None
					else:
						print("Inserting professor " + professor_name)
						professor_id = model.insert_professor(professor_name, 0)
				else:
					professor_id = professor['id']

			db.insert('grades',
				semester = semester,
				course_id = course_id,
				section = section,
				professor_id = professor_id,
				num_students = row['Total'],
				APLUS = row['A+'],
				A = row['A'],
				AMINUS = row['A-'],
				BPLUS = row['B+'],
				B = row['B'],
				BMINUS = row['B-'],
				CPLUS = row['C+'],
				C = row['C'],
				CMINUS = row['C-'],
				DPLUS = row['D+'],
				D = row['D'],
				DMINUS = row['D-'],
				F = row['Fs'],
				W = row['Withdraw'],
				OTHER = row['Other'])

print("==================")
insert_grades('202008')

