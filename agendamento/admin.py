from django.contrib import admin
from .models import User, Doctor, HealthPlan, Patient, Appointment


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['email']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'expertise', 'is_active']
    list_filter = ['is_active', 'expertise']
    search_fields = ['name', 'expertise']


@admin.register(HealthPlan)
class HealthPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'health_plan', 'is_active']
    list_filter = ['is_active', 'health_plan']
    search_fields = ['name', 'phone', 'user__email']
    raw_id_fields = ['user']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'doctor', 'patient', 'date', 'time', 'recurrence_type', 'is_active']
    list_filter = ['is_active', 'date', 'recurrence_type']
    search_fields = ['doctor__name', 'patient__name']
    date_hierarchy = 'date'
    raw_id_fields = ['doctor', 'patient']
