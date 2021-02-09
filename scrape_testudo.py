import re
from dataclasses import dataclass
import time
from datetime import datetime
import logging

from bs4 import BeautifulSoup
import requests
from datetime import datetime

import db


@dataclass
class Department():
    department_name: str
    courses: list["Course"]

@dataclass
class Course():
    course_name: str
    sections: list["Section"]

@dataclass
class Section():
    # Interestingly, a section id does not have to be a number, but can also be
    # a string (ex: ENGL393 section ESG1). We make all section ids strings for
    # homogeneity, and call them "names" instead of ids.
    section_name: str
    instructor_names: str
    total_seats: int
    open_seats: int
    waitlist_size: int
    holdfile_size: int


COURSES_URL = "https://app.testudo.umd.edu/soc/search?courseId={}&sectionId=" \
    "&termId=202101&_openSectionsOnly=on&creditCompare=%3E%3D&credits=0.0" \
    "&courseLevelFilter=ALL&instructor=&_facetoface=on&_blended=on&_online=on" \
    "&courseStartCompare=&courseStartHour=&courseStartMin=&courseStartAM=" \
    "&courseEndHour=&courseEndMin=&courseEndAM=&teachingCenter=ALL" \
    "&_classDay1=on&_classDay2=on&_classDay3=on&_classDay4=on&_classDay5=on"

DEPARTMENTS = ["INST", "MUSC", "THET", "NFSC", "AASP", "ENGL", "MIEH", "ENME",
    "CPGH", "ARTH", "PSYC", "GERM", "PHYS", "STAT", "KNES", "BIOE", "GEMS",
    "COMM", "CMSC", "JWST", "UNIV", "TDPS", "DANC", "JOUR", "ENEE", "HEBR",
    "PERS", "ENCE", "RELS", "HIST", "SPAN", "PHIL", "SOCY", "CCJS", "GEOL",
    "CPSD", "ASTR", "BMGT", "BUAC", "EDCI", "MEES", "BUFN", "EDHI", "ENTS",
    "FREN", "EDHD", "URSP", "EXST", "CLAS", "ENMA", "LING", "BSCI", "WMST",
    "HDCC", "AOSC", "ENPM", "CHEM", "MATH", "EDUC", "HESI", "ECON", "HONR",
    "GEOG", "PUAF", "ENAE", "CPSN", "FMSC", "ARSC", "BSOS", "HLTH", "ENES",
    "ANSC", "INAG", "CHBE", "BSST", "FIRE", "EDSP", "ENFP", "SLLC", "INFM",
    "IMMR", "ENST", "ARCH", "ARHU", "CHIN", "SURV", "HACS", "PLSC", "TLPL",
    "LARC", "BUDT", "UMEI", "MUED", "GVPT", "EDCP", "CBMG", "ENRE", "BUSI",
    "BIPH", "CHPH", "HLSA", "AMST", "ARTT", "BIOL", "BIOM", "CPET", "LBSC",
    "EDPS", "BCHM", "EPIB", "MLAW", "ENTM", "CLFS", "MUSP", "FILM", "ANTH",
    "RDEV", "HESP", "CMLT", "HISP", "AGNR", "RUSS", "AREC", "NACS", "BUMO",
    "ISRL", "ENSE", "BISI", "LASC", "CPSS", "CPSP", "ARAB", "ENCH", "CPPL",
    "AMSC", "CPSA", "LATN", "PHSC", "CPJT", "AAST", "JAPN", "ITAL", "BUMK",
    "BULM", "EDMS", "ENSP", "HHUM", "HLSC", "ENCO", "KORA", "CPMS", "BSCV",
    "HEIP", "LGBT", "CPSG", "MOCB", "GREK", "TOXI", "CONS", "SPHL", "ARMY",
    "ENNU", "BSGC", "CPBE", "VMSC", "SLAA", "FOLA", "USLT", "PORT", "CPSF",
    "EALL", "ENPP", "WINT", "MAIT", "FGSM", "MLSC", "NIAP", "NIAV", "SUMM",
    "BEES", "NAVY", "TLTC", "BUSM", "HLMN", "PEER", "IDEA", "MITH", "EMBA",
    "PLCY", "MSMC", "UGST", "MUET", "SLAV", "WEBS", "IVSP", "NIAS", "BUSO",
    "AAPS", "BERC", "DATA", "MSML", "PHPE", "NEUR", "HNUH", "SMLP", "BMSO",
    "AGST", "CHSE", "ENEB", "IMDM", "MSBB"]

courses_regex = re.compile("^[A-Z]{4}\d{3,}")

def take_snapshot():
    departments = []
    snapshots = []
    for department in DEPARTMENTS:
        print(f"{datetime.now()} loading department {department}")
        url = COURSES_URL.format(department)
        loaded = False
        while not loaded:
            try:
                text = requests.get(url).text
            except Exception as e:
                print(f"{datetime.now()} Exception while loading url {url}: {e}. Waiting for 10 seconds then retrying.")
                time.sleep(10)
                continue

            soup = BeautifulSoup(text, features="lxml")
            courses_page = soup.find(id="courses-page")
            if not courses_page:
                print(f"{datetime.now()} courses page element could not be found. Page html: {soup}. Waiting for 10 seconds then retrying.")
                time.sleep(10)
                continue

            loaded = True

        # some departments aren't offering any courses this semester, so move on
        # if this is the case
        if courses_page.find(class_="no-courses-message"):
            department = Department(department, [])
            departments.append(department)
            continue

        courses_soup = courses_page.find(class_="courses-container") \
                                   .find_all(id=courses_regex, recursive=False)

        courses = []
        for course in courses_soup:
            course_name = course["id"]
            sections_soup = course.find(class_="sections-container") \
                                  .find_all(class_="section")

            sections = []
            for section in sections_soup:
                # section name usually/always has tons of whitespace around it
                # for whatever reason, so strip it
                section_name = section.find(class_="section-id").string.strip()
                # there could be multiple instructors, each one will have its
                # own section-instructor class div
                instructors = section.find_all(class_="section-instructor")
                instructor_names = ", ".join(inst.string for inst in instructors)
                total_seats = int(section.find(class_="total-seats-count").string)
                open_seats = int(section.find(class_="open-seats-count").string)

                # If the waitlist is empty, there is only one element with this
                # class, which is the waitlist size (0).
                # If the waitlist is not empty, there are two elements with this
                # class. The first one is for the waitlist and the second one is
                # for the holdfile.
                waitlist_elems = list(section.find_all(class_="waitlist-count"))

                assert len(waitlist_elems) in [1, 2]

                if len(waitlist_elems) == 1:
                    assert int(waitlist_elems[0].string) == 0
                    waitlist_size = 0
                    holdfile_size = 0
                else:
                    waitlist_size = int(waitlist_elems[0].string)
                    holdfile_size = int(waitlist_elems[1].string)

                section = Section(section_name, instructor_names, total_seats,
                    open_seats, waitlist_size, holdfile_size)
                sections.append(section)

            course = Course(course_name, sections)
            courses.append(course)

        department = Department(department, courses)
        departments.append(department)

    return (departments, snapshots)

print(f"{datetime.now()} taking snapshot")
time_started = datetime.now()
(departments, snapshots) = take_snapshot()
print(f"{datetime.now()} starting saving")
print(f"{datetime.now()} saving departments")
for department in departments:
    db.write_department(department)

print(f"{datetime.now()} saved, committing")
db.commit(time_started)
print(f"{datetime.now()} committed")
