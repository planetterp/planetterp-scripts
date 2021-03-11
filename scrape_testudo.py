import requests
from bs4 import BeautifulSoup
import time
import model

def update_seats(semester):
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
				
				temp_course = model.get_course(course_name)
				if temp_course == None:
					print "Added course " + course_name
					course_id = model.insert_course(course_name[:4], course_name[4:])
					temp_course = model.get_course(course_name)
				else:
					course_id = temp_course['id']

				try:
					title = course.find_all(class_='course-title')[0].text
				except Exception:
					title = None

				description = ""
				
				description += "\n".join(d.get_text().strip() for d in course.find_all(class_='approved-course-text'))

				if description != "" and len(course.find_all(class_='course-text')) > 0:
					description += "\n"

				description += "\n".join("<i>" + d.text.strip() + "</i>" for d in course.find_all(class_='course-text'))
				description = description.replace("Prerequisite:", "\n<b>Prerequisite:</b>")
				description = description.replace("Corequisite:", "\n<b>Corequisite:</b>")
				description = description.replace("Recommended:", "\n<b>Recommended:</b>")
				description = description.replace("Restriction:", "\n<b>Restriction:</b>")
				description = description.replace("Formerly:", "\n<b>Formerly:</b>")
				description = description.replace("Cross-listed with:", "\n<b>Cross-listed with:</b>")
				description = description.replace("Credit only granted for:", "\n<b>Credit only granted for:</b>")
				description = description.replace("Additional information:", "\n<b>Additional information:</b>")

				description = description.strip()

				# Remove whitespace on each line
				temp_description = ""
				for line in description.split("\n"):
					temp_description += line.strip() + "\n"

				description = temp_description[:-1]

				if description == "":
					description = None

				credits = int(course.find_all(class_='course-min-credits')[-1].text)

				if (temp_course['title'] != title) or (temp_course['description'] != description) or (int(temp_course['credits']) != credits):
					# print "Description mismatch on {}:\n{}\n{}\n{}\n{}\n{}\n{}".format(course_name, temp_course['title'], title, temp_course['description'], description, temp_course['credits'], credits)
					print "Description mismatch on {}".format(course_name, temp_course['title'], title, temp_course['description'], description, temp_course['credits'], credits)
					model.update_course(course_id, title, description, credits)
			
			courses = courses[:-1] # Remove end comma

			page = requests.get('https://app.testudo.umd.edu/soc/' + semester + '/sections?courseIds=' + courses).text

			soup = BeautifulSoup(page, 'html.parser')

			for course in soup.find_all(class_='course-sections'):
				course_name = course['id']
				# print course_name

				course_id = model.get_course_id(course_name)

				for section in course.select('.delivery-f2f, .delivery-blended, .delivery-online'):
					section_id = -1

					s = section.find_all(class_='section-info-container')[0]
					professors = s.find_all(class_='section-instructors')[0].text.replace(", ", ",").split(",")
					
					professor_ids = ""

					for professor in professors:
						professor = professor.strip()
	
						p = model.get_professor_id(professor.encode('utf-8'))

						if not p and professor == "Instructor: TBA":
							p = 0
						elif not p:
							p = model.insert_professor(professor, 0)
							print "Added professor: " + professor

						if p != 0 and not model.professor_teaches_course(p, course_id):
							print "Professor " + professor + " teaches " + course_name
							model.insert_professor_course(p, course_id, semester)
						elif model.professor_teaches_course:
							model.update_professor_course_recent_semester(p, course_id, semester)
					
						professor_ids += str(p) + ","

					# professor_ids = professor_ids[:-1] # Remove last comma

					# section_number = s.find(class_='section-id').text.strip()

					# total_seats = s.find_all(class_="total-seats-count")[0].text.strip()
					# open_seats = s.find_all(class_="open-seats-count")[0].text.strip()
					# waitlist = s.find_all(class_="waitlist-count")[0].text.strip()

					# section_id = model.get_section_id(course_id, section_number)

					# if section_id:
					# 	model.update_section_seats(section_id, open_seats, waitlist, total_seats)
					# else:
					# 	section_id = model.insert_section(course_id, semester, section_number, professor_ids, total_seats, open_seats, waitlist)

					# meetings = section.find_all(class_='class-days-container')[0]

					# for meeting in meetings.find_all(class_='row'):
					# 	message = meeting.find_all(class_='class-message')
					# 	if len(message) > 0 and message[0].text == "Contact department or instructor for details.":
					# 		continue
					# 	elif len(message) > 0:
					# 		print message.text
					# 	meeting_days = meeting.find_all(class_='section-days')
					# 	if len(meeting_days) == 0 or meeting_days[0].text.strip() == "TBA":
					# 		continue

					# 	meeting_days = meeting_days[0].text.strip()

					# 	meeting_start_time = meeting.find_all(class_='class-start-time')[0].text.strip()
					# 	meeting_end_time = meeting.find_all(class_='class-end-time')[0].text.strip()
					# 	meeting_building = meeting.select('.building-code, .class-building')[0].text.strip()
					# 	if meeting_building == "TBA":
					# 		meeting_room = None
					# 	else:
					# 		try:
					# 			meeting_room = meeting.find_all(class_='class-room')[0].text.strip()
					# 		except IndexError:
					# 			meeting_room = None

					# 	meeting_type = meeting.find_all(class_='class-type')
					# 	if len(meeting_type) > 0:
					# 		if len(meeting_type) > 1:
					# 			print "check" + str(section_id)
					# 		meeting_type = meeting_type[0].text.strip()
					# 	else:
					# 		meeting_type = None

					# 	model.insert_section_meeting(section_id, meeting_days, meeting_start_time, meeting_end_time, meeting_building, meeting_room, meeting_type)
update_seats('202001')
update_seats('202005')
update_seats('202008')
update_seats('202012')
update_seats('202101')
update_seats('202105')
update_seats('202108')
update_seats('202108')



