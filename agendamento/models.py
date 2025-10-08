from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class Base(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, Base):
    email = models.EmailField(unique=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email


class Doctor(Base):
    name = models.CharField(max_length=100)
    expertise = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'


class HealthPlan(Base):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Health Plan'
        verbose_name_plural = 'Health Plans'


class Patient(Base):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=11)
    health_plan = models.ForeignKey(HealthPlan, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'


class Appointment(Base):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    recurrence_type = models.ForeignKey(HealthPlan, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'

    def __str__(self):
        return f'{self.doctor.name} - {self.patient.name} - {self.date} - {self.time}'
