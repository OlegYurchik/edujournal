class EntityContainer:
    def __init__(self, cls):
        self._cls = cls
        self._container = {}

    def check_type(function):
        def wrapper(self, value):
            if not isinstance(value, self._cls):
                return
            return function(self, value)
        return wrapper

    @check_type
    def __in__(self, value):
        return value.id in self._container

    def __iter__(self):
        return self._container.values().__iter__()

    @check_type
    def add(self, value):
        self._container[value.id] = value

    @check_type
    def remove(self, value):
        if value.id in self._container:
            del self._container[value.id]

    def clear(self):
        self._container.clear()

    def get(self, **kwargs):
        for entity in self:
            condition = True
            for attr, value in kwargs.items():
                condition = condition and entity.__dict__.get(attr) == value
            if condition:
                return entity

    def filter(self, **kwargs):
        results = []
        for entity in self:
            condition = True
            for attr, value in kwargs.items():
                condition = condition and entity.__dict__.get(attr) == value
            if condition:
                results.append(entity)
        return results


class ElementConstructor(type):
    def __new__(mcs, name, classes, fields):
        fields["_cache"] = {}
        return super().__new__(mcs, name, classes, fields)

    def __call__(cls, id, *args, **kwargs):
        if not id in cls._cache:
            cls._cache[id] = super().__call__(id, *args, **kwargs)
        else:
            cls._cache[id].update(*args, **kwargs)

        return cls._cache[id]

    def update(self, *args, **kwargs):
        raise NotImplementedError


class Entity(metaclass=ElementConstructor):
    pass


class Section(Entity):
    def __init__(self, id, name):
        self.id = id
        self.groups = EntityContainer(Group)
        self.update(name=name)

    def update(self, name):
        self.name = name


class Subject(Entity):
    def __init__(self, id, name):
        self.id = id
        self.update(name=name)

    def update(self, name):
        self.name = name


class Group(Entity):
    def __init__(self, id, name, section):
        self.id = id
        self.journals = EntityContainer(Journal)
        self.update(name=name, section=section)

    def update(self, name, section):
        self.name = name
        if hasattr(self, "section"):
            self.section.groups.remove(self)
        self.section = section
        self.section.groups.add(self)


class Journal(Entity):
    def __init__(self, id, group, subject):
        self.id = id
        self.students = EntityContainer(Student)
        self.lesson_types = EntityContainer(LessonType)
        self.lessons = EntityContainer(Lesson)
        self.control_types = EntityContainer(ControlType)
        self.controls = EntityContainer(Control)
        self.periods = EntityContainer(Period)
        self.mark_type_sections = EntityContainer(MarkTypeSection)
        self.mark_types = EntityContainer(MarkType)
        self.marks = EntityContainer(Mark)
        self.update(group=group, subject=subject)

    def update(self, group, subject):
        if hasattr(self, "group"):
            self.group.journals.remove(self)
        self.group = group
        self.group.journals.add(self)
        self.subject = subject


class Student(Entity):
    def __init__(self, id, name):
        self.id = id
        self.update(name=name)

    def update(self, name):
        self.name = name


class LessonType(Entity):
    def __init__(self, id, name):
        self.id = id
        self.update(name=name)

    def update(self, name):
        self.name = name


class Lesson(Entity):
    def __init__(self, id, number, theme, date):
        self.id = id
        self.update(number=number, theme=theme, date=date)

    def update(self, number, theme, date):
        self.number = number
        self.theme = theme
        self.date = date


class ControlType(Entity):
    def __init__(self, id, name, shortname, description):
        self.id = id
        self.update(name=name, shortname=shortname, description=description)

    def update(self, name, shortname, description):
        self.name = name
        self.shortname = shortname
        self.description = description


class Control(Entity):
    def __init__(self, id, control_type, lesson, text, short=None):
        self.id = id
        self.update(control_type=control_type, lesson=lesson, text=text, short=short)

    def update(self, control_type, lesson, text, short=None):
        self.type = control_type
        self.lesson = lesson
        self.text = text
        self.short = short

    @property
    def name(self):
        return self.type.name

    @property
    def shortname(self):
        return self.type.shortname

    @property
    def description(self):
        return self.type.description


class Period(Entity):
    def __init__(self, id, date_from, date_to):
        self.id = id
        self.update(date_from=date_from, date_to=date_to)

    def update(self, date_from, date_to):
        self.date_from = date_from
        self.date_to = date_to


class MarkTypeSection(Entity):
    def __init__(self, id, name, mask):
        self.id = id
        self.update(name=name, mask=mask)

    def update(self, name, mask):
        self.name = name
        self.mask = mask


class MarkType(MarkTypeSection):
    def __init__(self, id, name, shortname, mask):
        self.id = id
        self.update(name=name, shortname=shortname, mask=mask)

    def update(self, name, shortname, mask):
        self.name = name
        self.shortname = shortname
        self.mask = mask


class Mark(Entity):
    def __init__(self, id, mark_type, journal, student, control, text):
        self.id = id
        self.update(
            mark_type=mark_type,
            journal=journal,
            student=student,
            control=control,
            text=text,
        )

    def update(self, mark_type, journal, student, control, text):
        self.type = mark_type
        if hasattr(self, "journal"):
            self.journal.marks.remove(self)
        self.journal = journal
        self.journal.marks.add(self)
        self.student = student
        self.control = control
        self.text = text

    @property
    def name(self):
        return self.type.name

    @property
    def mask(self):
        return self.type.mask
