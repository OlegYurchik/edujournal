# SPB EduJournal

Библиотека для взаимодействия с Санкт-Петербургским Электронным Журналом для учителей

```python
from edujournal import Client


client = Client(host="https://sch333.online.petersburgedu.ru")
client.login(username="Логин", password="Пароль")

client.update()

for group in client.groups:
    journal = client.update_journal(journal)

    for student in journal.students:
        print(student.name)
```