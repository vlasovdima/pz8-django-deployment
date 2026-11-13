from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import Course, CourseEnrollment, Department, StudentProfile

MONTH_NAMES_RU = {
    1: 'Янв', 2: 'Фев', 3: 'Мар', 4: 'Апр',
    5: 'Май', 6: 'Июн', 7: 'Июл', 8: 'Авг',
    9: 'Сен', 10: 'Окт', 11: 'Ноя', 12: 'Дек',
}


def _short_dept_name(name):
    """Сокращает длинное название факультета для подписей на осях графиков."""
    if len(name) <= 24:
        return name
    return name[:22].rstrip() + '…'


def _parse_int(value):
    """Безопасно переводит строку GET-параметра в целое число."""
    if value and str(value).isdigit():
        return int(value)
    return None


def _filter_enrollments(dept_id=None, period_days=None, status=None):
    """Общая фильтрация записей на курсы для всех дашбордов."""
    qs = CourseEnrollment.objects.select_related('student__user', 'student__department', 'course__department')

    if dept_id:
        qs = qs.filter(Q(course__department_id=dept_id) | Q(student__department_id=dept_id))

    if period_days and period_days > 0:
        since = timezone.now() - timedelta(days=period_days)
        qs = qs.filter(enrolled_at__gte=since)

    if status in ('active', 'completed', 'dropped'):
        qs = qs.filter(status=status)

    return qs


def build_overview_data(dept_id=None, period_days=None, status=None):
    """Собирает показатели и графики для дашборда 1 (Общая сводка портала)."""
    dept_num = _parse_int(dept_id)
    period_num = _parse_int(period_days)

    students_qs = StudentProfile.objects.all()
    courses_qs = Course.objects.all()
    depts_qs = Department.objects.all()

    if dept_num:
        students_qs = students_qs.filter(department_id=dept_num)
        courses_qs = courses_qs.filter(department_id=dept_num)
        depts_qs = depts_qs.filter(id=dept_num)

    enrollments_qs = _filter_enrollments(dept_num, period_num, status)
    active_enrollments = enrollments_qs.filter(status__in=['active', 'completed'])

    avg_progress_raw = active_enrollments.aggregate(val=Avg('progress'))['val']
    avg_progress = round(avg_progress_raw, 1) if avg_progress_raw is not None else 0

    kpis = {
        'students_count': students_qs.count(),
        'courses_count': courses_qs.count(),
        'enrollments_count': active_enrollments.count(),
        'avg_progress': f'{avg_progress}%',
    }

    # График 1: Динамика записей по месяцам (реальные даты из CourseEnrollment)
    monthly_qs = (
        enrollments_qs
        .annotate(month=TruncMonth('enrolled_at'))
        .values('month')
        .annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
        )
        .order_by('month')
    )

    timeline_labels = []
    timeline_total = []
    timeline_completed = []
    for row in monthly_qs:
        dt = row['month']
        if dt:
            timeline_labels.append(f"{MONTH_NAMES_RU.get(dt.month, dt.month)} {dt.year}")
            timeline_total.append(row['total'])
            timeline_completed.append(row['completed'])

    # График 2: Распределение студентов по факультетам
    dept_stats = depts_qs.annotate(
        students_cnt=Count('students', distinct=True),
        courses_cnt=Count('courses', distinct=True),
        enrollments_cnt=Count(
            'courses__enrollments',
            filter=Q(courses__enrollments__status__in=['active', 'completed']),
            distinct=True,
        ),
    ).order_by('name')

    dept_labels = [_short_dept_name(d.name) for d in dept_stats]
    dept_students = [d.students_cnt for d in dept_stats]
    dept_courses = [d.courses_cnt for d in dept_stats]
    dept_enrollments = [d.enrollments_cnt for d in dept_stats]

    # Таблица последних записей (живые данные из БД)
    recent_rows = []
    for item in enrollments_qs.order_by('-enrolled_at')[:8]:
        recent_rows.append({
            'student': item.student.user.get_full_name() or item.student.user.username,
            'username': item.student.user.username,
            'course': item.course.title,
            'department': _short_dept_name(item.course.department.name),
            'progress': item.progress,
            'status': item.status,
            'status_label': item.get_status_display(),
            'enrolled_at': timezone.localtime(item.enrolled_at).strftime('%d.%m.%Y'),
        })

    return {
        'kpis': kpis,
        'charts': {
            'timeline': {
                'labels': timeline_labels,
                'total': timeline_total,
                'completed': timeline_completed,
            },
            'dept_distribution': {
                'labels': dept_labels,
                'values': dept_students,
            },
            'dept_comparison': {
                'labels': dept_labels,
                'courses': dept_courses,
                'enrollments': dept_enrollments,
            },
        },
        'recent_rows': recent_rows,
    }


def build_courses_data(dept_id=None, level=None, query=None):
    """Собирает аналитику по учебным курсам для дашборда 2."""
    dept_num = _parse_int(dept_id)
    courses_qs = Course.objects.select_related('department')

    if dept_num:
        courses_qs = courses_qs.filter(department_id=dept_num)

    if level in ('bachelor', 'master', 'elective'):
        courses_qs = courses_qs.filter(level=level)

    if query:
        q_clean = query.strip()
        if q_clean:
            courses_qs = courses_qs.filter(
                Q(title__icontains=q_clean) | Q(description__icontains=q_clean)
            )

    annotated_courses = courses_qs.annotate(
        active_cnt=Count('enrollments', filter=Q(enrollments__status__in=['active', 'completed'])),
        completed_cnt=Count('enrollments', filter=Q(enrollments__status='completed')),
        avg_prog=Avg('enrollments__progress', filter=Q(enrollments__status__in=['active', 'completed'])),
    ).order_by('-active_cnt', 'title')

    courses_list = list(annotated_courses)
    total_courses = len(courses_list)
    total_hours = sum(c.hours for c in courses_list)
    total_active = sum(c.active_cnt for c in courses_list)
    total_completed = sum(c.completed_cnt for c in courses_list)

    top_course = courses_list[0].title if courses_list else 'Нет данных'
    if len(top_course) > 22:
        top_course = top_course[:20].rstrip() + '…'

    avg_students_per_course = round(total_active / total_courses, 1) if total_courses else 0
    completion_rate = round((total_completed / total_active) * 100, 1) if total_active else 0

    kpis = {
        'top_course': top_course,
        'avg_per_course': avg_students_per_course,
        'total_hours': total_hours,
        'completion_rate': f'{completion_rate}%',
    }

    # График 1: Топ-8 курсов по количеству записанных студентов
    top_slice = courses_list[:8]
    popularity_labels = [c.title[:26] + ('…' if len(c.title) > 26 else '') for c in top_slice]
    popularity_values = [c.active_cnt for c in top_slice]

    # График 2: Распределение курсов по уровням подготовки
    level_map = dict(Course.LEVEL_CHOICES)
    level_counts = courses_qs.values('level').annotate(cnt=Count('id')).order_by('level')
    level_labels = [level_map.get(item['level'], item['level']) for item in level_counts]
    level_values = [item['cnt'] for item in level_counts]

    # График 3: Средний прогресс по курсам
    progress_labels = [c.title[:20] + ('…' if len(c.title) > 20 else '') for c in top_slice]
    progress_values = [round(c.avg_prog, 1) if c.avg_prog is not None else 0 for c in top_slice]

    table_rows = []
    for c in courses_list:
        avg_p = round(c.avg_prog, 1) if c.avg_prog is not None else 0
        table_rows.append({
            'id': c.id,
            'title': c.title,
            'department': _short_dept_name(c.department.name),
            'level_label': c.get_level_display(),
            'hours': c.hours,
            'credits': c.credits,
            'active_cnt': c.active_cnt,
            'completed_cnt': c.completed_cnt,
            'avg_progress': avg_p,
        })

    return {
        'kpis': kpis,
        'charts': {
            'popularity': {
                'labels': popularity_labels,
                'values': popularity_values,
            },
            'levels': {
                'labels': level_labels,
                'values': level_values,
            },
            'course_progress': {
                'labels': progress_labels,
                'values': progress_values,
            },
        },
        'table_rows': table_rows,
    }


def build_students_data(dept_id=None, status=None):
    """Собирает аналитику активности и успеваемости студентов для дашборда 3."""
    dept_num = _parse_int(dept_id)
    students_qs = StudentProfile.objects.select_related('user', 'department')
    if dept_num:
        students_qs = students_qs.filter(department_id=dept_num)

    enrollments_qs = _filter_enrollments(dept_num, None, status)

    # Аннотация по каждому студенту
    students_annotated = students_qs.annotate(
        active_courses=Count(
            'enrollments',
            filter=Q(enrollments__status__in=['active', 'completed']),
            distinct=True,
        ),
        completed_courses=Count(
            'enrollments',
            filter=Q(enrollments__status='completed'),
            distinct=True,
        ),
        avg_progress=Avg(
            'enrollments__progress',
            filter=Q(enrollments__status__in=['active', 'completed']),
        ),
        avg_grade=Avg(
            'enrollments__grade',
            filter=Q(enrollments__grade__isnull=False),
        ),
    ).order_by('-active_courses', '-avg_progress', 'user__username')

    students_list = list(students_annotated)
    total_students = len(students_list)
    active_students = sum(1 for s in students_list if s.active_courses > 0)
    total_courses_taken = sum(s.active_courses for s in students_list)
    total_completed = sum(s.completed_courses for s in students_list)

    avg_courses = round(total_courses_taken / total_students, 1) if total_students else 0
    avg_grade_raw = enrollments_qs.filter(grade__isnull=False).aggregate(val=Avg('grade'))['val']
    avg_grade = round(avg_grade_raw, 2) if avg_grade_raw is not None else 0

    kpis = {
        'active_students': active_students,
        'avg_courses': avg_courses,
        'avg_grade': avg_grade if avg_grade else '—',
        'completed_total': total_completed,
    }

    # График 1: Распределение статусов записей (В процессе / Завершён / Отписан)
    status_map = dict(CourseEnrollment.STATUS_CHOICES)
    status_counts = enrollments_qs.values('status').annotate(cnt=Count('id')).order_by('status')
    status_labels = [status_map.get(row['status'], row['status']) for row in status_counts]
    status_values = [row['cnt'] for row in status_counts]

    # График 2: Распределение студентов по числу курсов (0, 1, 2, 3+)
    buckets = {'0 курсов': 0, '1 курс': 0, '2 курса': 0, '3+ курса': 0}
    for s in students_list:
        if s.active_courses == 0:
            buckets['0 курсов'] += 1
        elif s.active_courses == 1:
            buckets['1 курс'] += 1
        elif s.active_courses == 2:
            buckets['2 курса'] += 1
        else:
            buckets['3+ курса'] += 1

    # График 3: Средний прогресс студентов по факультетам
    depts_qs = Department.objects.all()
    if dept_num:
        depts_qs = depts_qs.filter(id=dept_num)
    dept_prog = depts_qs.annotate(
        avg_p=Avg(
            'students__enrollments__progress',
            filter=Q(students__enrollments__status__in=['active', 'completed']),
        )
    ).order_by('name')

    dept_labels = [_short_dept_name(d.name) for d in dept_prog]
    dept_avg_progress = [round(d.avg_p, 1) if d.avg_p is not None else 0 for d in dept_prog]

    leaderboard = []
    for s in students_list:
        avg_p = round(s.avg_progress, 1) if s.avg_progress is not None else 0
        avg_g = round(s.avg_grade, 2) if s.avg_grade is not None else '—'
        leaderboard.append({
            'name': s.user.get_full_name() or s.user.username,
            'username': s.user.username,
            'department': _short_dept_name(s.department.name) if s.department else 'Не указан',
            'active_courses': s.active_courses,
            'completed_courses': s.completed_courses,
            'avg_progress': avg_p,
            'avg_grade': avg_g,
        })

    return {
        'kpis': kpis,
        'charts': {
            'status_breakdown': {
                'labels': status_labels,
                'values': status_values,
            },
            'workload_buckets': {
                'labels': list(buckets.keys()),
                'values': list(buckets.values()),
            },
            'dept_progress': {
                'labels': dept_labels,
                'values': dept_avg_progress,
            },
        },
        'leaderboard': leaderboard,
    }
