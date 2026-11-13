from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Course, CourseEnrollment, Department, StudentProfile


class Command(BaseCommand):
    help = 'Заполняет базу демонстрационными факультетами, курсами, студентами и записями для дашбордов.'

    def handle(self, *args, **options):
        dept_it, _ = Department.objects.get_or_create(
            name='Институт №3 «Системы управления, информатика и электроэнергетика»'
        )
        dept_math, _ = Department.objects.get_or_create(
            name='Кафедра 317 «Инноватика»'
        )
        dept_econ, _ = Department.objects.get_or_create(
            name='Институт инженерной экономики и гуманитарных наук'
        )
        dept_aero, _ = Department.objects.get_or_create(
            name='Институт №1 «Авиационная техника»'
        )

        # (название, описание, факультет, часы, з.е., уровень)
        courses_data = [
            (
                'Структура программного обеспечения и базы данных',
                'Проектирование реляционных БД, Django ORM, миграции и интерфейсы на Tabler.',
                dept_math, 144, 4, 'bachelor',
            ),
            (
                'Программирование на Python',
                'Базовые структуры данных, ООП, работа с файлами и веб-фреймворками.',
                dept_it, 108, 3, 'bachelor',
            ),
            (
                'Веб-технологии и адаптивная верстка',
                'HTML5, CSS3, Bootstrap 5, сетки и динамические компоненты интерфейса.',
                dept_it, 108, 3, 'bachelor',
            ),
            (
                'Управление инновационными проектами',
                'Жизненный цикл продукта, оценка рисков и планирование ресурсов.',
                dept_math, 144, 4, 'master',
            ),
            (
                'Системный анализ и моделирование',
                'Построение диаграмм процессов, нотации BPMN и UML.',
                dept_it, 108, 3, 'bachelor',
            ),
            (
                'Экономика программной инженерии',
                'Оценка трудоемкости разработки и расчет эффективности ИТ-решений.',
                dept_econ, 72, 2, 'bachelor',
            ),
            (
                'Машинное обучение и анализ данных',
                'Методы классификации, регрессии и визуализация результатов в Python.',
                dept_it, 180, 5, 'master',
            ),
            (
                'Цифровые двойники в авиастроении',
                'Моделирование изделий и сбор телеметрии в реальном времени.',
                dept_aero, 144, 4, 'master',
            ),
            (
                'Технологическое предпринимательство',
                'Вывод ИТ-продуктов на рынок и оценка инвестиционной привлекательности.',
                dept_econ, 72, 2, 'elective',
            ),
            (
                'Проектный практикум по аналитике данных',
                'Построение интерактивных дашбордов и метрик качества процессов.',
                dept_math, 108, 3, 'elective',
            ),
        ]

        courses = []
        for title, desc, dept, hours, credits, level in courses_data:
            course, created = Course.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc,
                    'department': dept,
                    'hours': hours,
                    'credits': credits,
                    'level': level,
                },
            )
            if not created:
                # Обновляем поля нагрузки на случай повторного запуска сида
                course.hours = hours
                course.credits = credits
                course.level = level
                course.save(update_fields=['hours', 'credits', 'level'])
            courses.append(course)

        # Список студентов: (username, first_name, last_name, department)
        students_spec = [
            ('student1', 'Дмитрий', 'Власов', dept_math),
            ('student2', 'Алексей', 'Смирнов', dept_it),
            ('student3', 'Екатерина', 'Соколова', dept_math),
            ('student4', 'Максим', 'Кузнецов', dept_it),
            ('student5', 'Анна', 'Попова', dept_econ),
            ('student6', 'Иван', 'Морозов', dept_aero),
            ('student7', 'Мария', 'Волкова', dept_math),
            ('student8', 'Артём', 'Новиков', dept_it),
            ('student9', 'Ольга', 'Лебедева', dept_econ),
            ('student10', 'Никита', 'Козлов', dept_aero),
            ('student11', 'Дарья', 'Павлова', dept_math),
            ('student12', 'Сергей', 'Орлов', dept_it),
        ]

        profiles = {}
        for uname, fname, lname, dept in students_spec:
            user, u_created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f'{uname}@mai.local',
                    'first_name': fname,
                    'last_name': lname,
                },
            )
            if u_created:
                user.set_password('Student123!')
                user.save()

            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={'department': dept},
            )
            if profile.department is None:
                profile.department = dept
                profile.save(update_fields=['department'])
            profiles[uname] = profile

        # Если записей CourseEnrollment ещё нет — формируем реалистичную историю за 180 дней
        if not CourseEnrollment.objects.exists():
            now = timezone.now()
            enrollment_plan = [
                # (username, course_idx, days_ago, progress, status, grade)
                ('student1', 0, 145, 100, 'completed', 5),
                ('student1', 1, 110, 85, 'active', None),
                ('student1', 2, 62, 60, 'active', None),
                ('student1', 9, 18, 40, 'active', None),

                ('student2', 1, 160, 100, 'completed', 5),
                ('student2', 4, 95, 75, 'active', None),
                ('student2', 6, 30, 50, 'active', None),

                ('student3', 0, 150, 100, 'completed', 5),
                ('student3', 3, 120, 100, 'completed', 4),
                ('student3', 9, 45, 70, 'active', None),
                ('student3', 5, 80, 20, 'dropped', None),

                ('student4', 1, 140, 100, 'completed', 4),
                ('student4', 2, 100, 90, 'active', None),
                ('student4', 4, 55, 65, 'active', None),
                ('student4', 6, 12, 30, 'active', None),

                ('student5', 5, 155, 100, 'completed', 5),
                ('student5', 8, 90, 80, 'active', None),
                ('student5', 3, 40, 45, 'active', None),

                ('student6', 7, 130, 100, 'completed', 4),
                ('student6', 4, 70, 55, 'active', None),
                ('student6', 0, 25, 35, 'active', None),

                ('student7', 0, 125, 100, 'completed', 5),
                ('student7', 3, 85, 95, 'active', None),
                ('student7', 9, 15, 50, 'active', None),

                ('student8', 1, 115, 70, 'active', None),
                ('student8', 2, 75, 15, 'dropped', None),
                ('student8', 6, 22, 60, 'active', None),

                ('student9', 5, 105, 100, 'completed', 4),
                ('student9', 8, 50, 65, 'active', None),

                ('student10', 7, 92, 80, 'active', None),
                ('student10', 1, 35, 45, 'active', None),

                ('student11', 0, 68, 85, 'active', None),
                ('student11', 9, 10, 25, 'active', None),
                ('student11', 3, 148, 100, 'completed', 5),

                ('student12', 2, 58, 55, 'active', None),
                ('student12', 4, 28, 30, 'active', None),
            ]

            for uname, c_idx, days_ago, progress, status, grade in enrollment_plan:
                prof = profiles[uname]
                course = courses[c_idx]
                CourseEnrollment.objects.create(
                    student=prof,
                    course=course,
                    enrolled_at=now - timedelta(days=days_ago),
                    progress=progress,
                    status=status,
                    grade=grade,
                )
                if status in ('active', 'completed'):
                    prof.courses.add(course)

        # Администратор для проверки админ-панели
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@mai.local', 'Admin123!')

        self.stdout.write(self.style.SUCCESS('Демо-данные для ПЗ №6 успешно загружены.'))
