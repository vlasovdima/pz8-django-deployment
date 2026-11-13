from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/toggle/', views.toggle_course_enrollment, name='toggle_course'),
    path('departments/', views.department_list, name='department_list'),
]
