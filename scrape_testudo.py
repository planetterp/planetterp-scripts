from bs4 import BeautifulSoup
import requests
import re
from dataclasses import dataclass
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
    instructor: str

@dataclass
class Snapshot():
    course_name: str
    section_name: str
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

DEPARTMNETS = ["INST", "MUSC", "THET", "NFSC", "AASP", "ENGL", "MIEH", "ENME",
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

DEPARTMNETS = ["CMSC"]
courses_regex = re.compile("^[A-Z]{4}\d{3,}")


db.create_db()

def take_snapshot():
    departments = []
    snapshots = []
    for department in DEPARTMNETS:
        url = COURSES_URL.format(department)
        text = requests.get(url).text
        soup = BeautifulSoup(text, features="lxml")

        courses_page = soup.find(id="courses-page")

        # some departments aren't offering any courses this semester, so move on if
        # this is the case
        if courses_page.find(class_="no-courses-message"):
            print(f"{department} is not offering any classes")
            department = Department(department)
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
                instructor = section.find(class_="section-instructor").string
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

                section = Section(section_name, instructor)
                snapshot = Snapshot(course_name, section_name, total_seats,
                    open_seats, waitlist_size, holdfile_size)
                sections.append(section)
                snapshots.append(snapshot)

            course = Course(course_name, sections)
            courses.append(course)

        department = Department(department, courses)
        departments.append(department)

    return (departments, snapshots)

(departments, snapshots) = take_snapshot()
for department in departments:
    db.add_department_if_not_exists(department)

for snapshot in snapshots:
    db.save_snapshot(snapshot)

db.commit()
