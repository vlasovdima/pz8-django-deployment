from django.contrib import admin

from .models import Course, CourseEnrollment, Department, StudentProfile


# Отображение списка факультетов с поиском по названию
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


# Настройка панели курсов: фильтр по факультету, уровню и поиск по названию
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'department', 'level', 'hours', 'credits')
    list_filter = ('department', 'level')
    search_fields = ('title',)


# Панель профилей студентов с горизонтальным виджетом выбора курсов (N:M)
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'department')
    list_filter = ('department',)
    search_fields = ('user__username',)
    filter_horizontal = ('courses',)


# Журнал записей на курсы с прогрессом и оценками
@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course', 'status', 'progress', 'grade', 'enrolled_at')
    list_filter = ('status', 'course__department')
    search_fields = ('student__user__username', 'course__title')
