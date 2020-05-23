import datetime
import requests
from urllib.parse import urljoin

from .entities import (Control, ControlType, EntityContainer, Group, Journal, Lesson, LessonType,
                       Mark, MarkType, MarkTypeSection, Period, Section, Student, Subject) 
from .exceptions import EDUJournalException


class Client:
    EXECUTE_URL = "/webservice/app.cj2/execute"

    def __init__(self, host):
        self.host = host
        self._session = requests.Session()
        self._sections = EntityContainer(Section)
        self._subjects = EntityContainer(Subject)
        self._groups = EntityContainer(Group)
        self._journals = EntityContainer(Journal)

    def __del__(self):
        self._session.close()

    @property
    def sections(self):
        return self._sections

    @property
    def subjects(self):
        return self._subjects

    @property
    def groups(self):
        return self._groups

    @property
    def journals(self):
        return self._journals

    def login(self, username, password):
        url = urljoin(self.host, "/login")

        response = self._session.post(
            url=url,
            params={"user-name": username, "user-password": password},
        )
        response.raise_for_status()
        data = response.json()

        if "verified" not in data:
            raise EDUJournalException("Incorrect response by login: %s" % response.content)
        if data["verified"] == 0:
            raise EDUJournalException("Incorrect username or/and password")

    def update(self):
        url = urljoin(self.host, self.EXECUTE_URL)

        response = self._session.get(
            url=url,
            params={"action": "menu"},
        )
        response.raise_for_status()
        payload = response.json()

        self._sections.clear()
        self._subjects.clear()
        self._groups.clear()
        self._journals.clear()

        for section_payload in payload:
            section = Section(
                id=section_payload["id"],
                name=section_payload["name"],
            )
            self._sections.add(section)

            for subject_payload in section_payload["items"]:
                subject = Subject(
                    id=subject_payload["id"],
                    name=subject_payload["name"],
                )
                self._subjects.add(subject)

                for journal_payload in subject_payload["items"]:
                    group = Group(
                        id=journal_payload["grade_id"],
                        name=journal_payload["name"],
                        section=section,
                    )
                    self._groups.add(group)

                    journal = Journal(
                        id=journal_payload["id"],
                        group=group,
                        subject=subject,
                    )
                    self._journals.add(journal)

    def update_journal(self, journal):
        url = urljoin(self.host, self.EXECUTE_URL)
        
        response = self._session.get(
            url=url,
            params={"action": "getdata", "id": journal.id},
        )
        response.raise_for_status()
        payload = response.json()

        journal_payload = payload["journal"]
        journal.update(
            group=self.groups.get(id=journal_payload["grade_id"]),
            subject=self.subjects.get(id=journal_payload["subject_id"]),
        )

        journal.students.clear()
        for student_payload in payload["members"]:
            student = Student(
                id=student_payload["id"],
                name=student_payload["name"],
            )
            journal.students.add(student)

        journal.lesson_types.clear()
        for lesson_type_payload in payload["lesson_types"]:
            lesson_type = LessonType(
                id=lesson_type_payload["id"],
                name=lesson_type_payload["name"],
            )
            journal.lesson_types.add(lesson_type)

        journal.lessons.clear()
        for lesson_payload in payload["lessons"]:
            lesson = Lesson(
                id=lesson_payload["id"],
                number=lesson_payload["num"],
                theme=lesson_payload.get("theme"),
                date=datetime.datetime.strptime(lesson_payload["date"], "%Y-%m-%d"),
            )
            journal.lessons.add(lesson)

        journal.control_types.clear()
        for control_type_payload in payload["control_types"]:
            control_type = ControlType(
                id=control_type_payload["id"],
                name=control_type_payload["name"],
                shortname=control_type_payload["shortname"],
                description=control_type_payload["desc"],
            )
            journal.control_types.add(control_type)

        journal.controls.clear()
        for control_payload in payload["controls"]:
            control = Control(
                id=control_payload["id"],
                control_type=control_payload["type_id"],  # Fast
                lesson=journal.lessons.get(id=control_payload["lesson_id"]),
                text=control_payload["text"],
                short=control_payload.get("short"),
            )
            journal.controls.add(control)

        journal.periods.clear()
        for period_payload in payload["periods"]:
            period = Period(
                id=period_payload["type_id"],
                date_from=datetime.datetime.strptime(period_payload["date_from"], "%Y-%m-%d"),
                date_to=datetime.datetime.strptime(period_payload["date_to"], "%Y-%m-%d"),
            )
            journal.periods.add(period)

        journal.mark_type_sections.clear()
        journal.mark_types.clear()
        for mark_type_section_payload in payload["mark_types"]:
            mark_type_section = MarkTypeSection(
                id=mark_type_section_payload["id"],
                name=mark_type_section_payload["name"],
                mask=mark_type_section_payload["mask"],
            )
            journal.mark_type_sections.add(mark_type_section)

            for mark_type_payload in mark_type_section_payload["marks"]:
                mark_type = MarkType(
                    id=mark_type_payload["id"],
                    name=mark_type_payload["name"],
                    shortname=mark_type_payload["shortname"],
                    mask=mark_type_payload["mask"],
                )
                journal.mark_types.add(mark_type)

        journal.marks.clear()
        for mark_payload in payload["marks"]:
            mark_type = journal.mark_types.get(id=mark_payload["type_id"])
            if mark_type is None:
                mark_type = journal.mark_type_sections.get(id=mark_payload["type_id"])
            mark = Mark(
                id=mark_payload["id"],
                mark_type=mark_type,
                journal=journal,
                student=journal.students.get(id=mark_payload["student_id"]),
                control=journal.controls.get(id=mark_payload["control_id"]),
                text=mark_payload["text"],
            )
            journal.marks.add(mark)

        return journal
