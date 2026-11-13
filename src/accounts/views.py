from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Course, Department, StudentProfile


def home(request):
    """Главная страница учебного портала с общей сводкой по факультетам и курсам."""
    departments = Department.objects.annotate(
        courses_cnt=Count('courses', distinct=True),
        students_cnt=Count('students', distinct=True),
    ).order_by('name')

    recent_courses = Course.objects.select_related('department').annotate(
        students_cnt=Count('students', distinct=True)
    ).order_by('-id')[:6]

    context = {
        'departments': departments,
        'recent_courses': recent_courses,
        'departments_count': departments.count(),
        'courses_count': Course.objects.count(),
        'students_count': StudentProfile.objects.count(),
    }
    return render(request, 'home.html', context)


@login_required
def profile(request):
    """Личный кабинет студента с выбором факультета и списком его курсов."""
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        dept_id = request.POST.get('department_id', '').strip()
        if dept_id:
            dept = get_object_or_404(Department, id=dept_id)
            student_profile.department = dept
            student_profile.save()
            messages.success(request, f'Факультет обновлён: {dept.name}')
        else:
            student_profile.department = None
            student_profile.save()
            messages.info(request, 'Привязка к факультету снята.')
        return redirect('profile')

    departments = Department.objects.order_by('name')
    enrolled_courses = student_profile.courses.select_related('department').order_by('title')

    return render(
        request,
        'profile.html',
        {
            'student_profile': student_profile,
            'departments': departments,
            'enrolled_courses': enrolled_courses,
        },
    )


@login_required
def course_list(request):
    """Каталог учебных курсов с поиском по названию и фильтром по факультету."""
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('dept', '').strip()

    courses = Course.objects.select_related('department').annotate(
        students_cnt=Count('students', distinct=True)
    ).order_by('title')

    if query:
        courses = courses.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    selected_dept = None
    if dept_id.isdigit():
        selected_dept = int(dept_id)
        courses = courses.filter(department_id=selected_dept)

    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    enrolled_ids = set(student_profile.courses.values_list('id', flat=True))
    departments = Department.objects.order_by('name')

    return render(
        request,
        'course_list.html',
        {
            'courses': courses,
            'departments': departments,
            'enrolled_ids': enrolled_ids,
            'query': query,
            'selected_dept': selected_dept,
        },
    )


@login_required
@require_POST
def toggle_course_enrollment(request, course_id):
    """Запись студента на курс или отписка от него."""
    course = get_object_or_404(Course, id=course_id)
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if student_profile.courses.filter(id=course.id).exists():
        student_profile.courses.remove(course)
        messages.info(request, f'Вы отписались от курса «{course.title}».')
    else:
        student_profile.courses.add(course)
        messages.success(request, f'Вы записались на курс «{course.title}».')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/courses/'
    return redirect(next_url)


@login_required
def department_list(request):
    """Список факультетов и закреплённых за ними учебных дисциплин."""
    departments = Department.objects.prefetch_related('courses').annotate(
        courses_cnt=Count('courses', distinct=True),
        students_cnt=Count('students', distinct=True),
    ).order_by('name')

    return render(
        request,
        'department_list.html',
        {
            'departments': departments,
        },
    )
