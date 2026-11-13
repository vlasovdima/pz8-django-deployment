from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# Факультет (кафедра/направление), к которому привязаны курсы и студенты
class Department(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


# Учебная дисциплина (курс), связанная с факультетом связью 1 : N
class Course(models.Model):
    LEVEL_CHOICES = [
        ('bachelor', 'Бакалавриат'),
        ('master', 'Магистратура'),
        ('elective', 'Факультатив'),
    ]

    title = models.CharField(max_length=200)

    description = models.TextField(
        blank=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses'
    )

    hours = models.PositiveIntegerField(default=72)
    credits = models.PositiveSmallIntegerField(default=3)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='bachelor')

    def __str__(self):
        return self.title


# Профиль студента: расширяет модель User (1 : 1) и хранит список выбранных курсов (N : M)
class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    courses = models.ManyToManyField(
        Course,
        blank=True,
        related_name='students'
    )

    def __str__(self):
        return self.user.username


# Запись студента на курс с датой, прогрессом и статусом для аналитики
class CourseEnrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'В процессе'),
        ('completed', 'Завершён'),
        ('dropped', 'Отписан'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(default=timezone.now)
    progress = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    grade = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.student.user.username} -> {self.course.title} ({self.progress}%)'
