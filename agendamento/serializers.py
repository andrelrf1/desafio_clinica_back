from rest_framework import serializers
from .models import User, Doctor, HealthPlan, Patient, Appointment
from datetime import datetime, time, timedelta


class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'is_active', 'created_at']
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'is_active', 'created_at']
        read_only_fields = fields


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'expertise', 'is_active']
        read_only_fields = fields


class HealthPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthPlan
        fields = ['id', 'name', 'is_active']
        read_only_fields = fields


class PatientSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    health_plan_name = serializers.CharField(source='health_plan.name', read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'name', 'phone', 'user_email', 'health_plan_name', 'is_active']
        read_only_fields = fields


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    doctor_expertise = serializers.CharField(source='doctor.expertise', read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    recurrence_name = serializers.CharField(source='recurrence_type.name', read_only=True)

    CONSULTATION_DURATION = 40

    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'doctor_expertise',
            'patient',
            'patient_name',
            'date',
            'time',
            'recurrence_type',
            'recurrence_name',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'doctor_name', 'doctor_expertise', 'patient_name',
                            'recurrence_name']

    def validate_date(self, value):
        if value < datetime.now().date():
            raise serializers.ValidationError("Não é possível agendar para uma data passada.")
        return value

    def validate_time(self, value):
        if value < time(8, 0) or value >= time(18, 0):
            raise serializers.ValidationError("Horário deve estar entre 08:00 e 18:00.")

        consultation_datetime = datetime.combine(datetime.today(), value)
        end_time = (consultation_datetime + timedelta(minutes=self.CONSULTATION_DURATION)).time()

        if end_time > time(18, 0):
            raise serializers.ValidationError(
                f"A consulta tem duração de {self.CONSULTATION_DURATION} minutos. "
                f"Este horário faria a consulta terminar após às 18:00."
            )

        return value

    def _check_time_overlap(self, start_time, existing_time):
        today = datetime.today()
        new_start = datetime.combine(today, start_time)
        new_end = new_start + timedelta(minutes=self.CONSULTATION_DURATION)

        existing_start = datetime.combine(today, existing_time)
        existing_end = existing_start + timedelta(minutes=self.CONSULTATION_DURATION)

        return (
            (new_start < existing_end and new_end > existing_start)
        )

    def validate(self, data):
        base_qs = Appointment.objects.filter(
            is_active=True,
            date=data['date']
        )

        conflitos_medico = base_qs.filter(doctor=data['doctor'])

        if self.instance:
            conflitos_medico = conflitos_medico.exclude(pk=self.instance.pk)

        for consulta in conflitos_medico:
            if self._check_time_overlap(data['time'], consulta.time):
                consulta_datetime = datetime.combine(datetime.today(), consulta.time)
                consulta_fim = (consulta_datetime + timedelta(minutes=self.CONSULTATION_DURATION)).time()

                raise serializers.ValidationError({
                    'time': (
                        f'Conflito de horário! O médico já tem uma consulta às {consulta.time.strftime("%H:%M")} '
                        f'(termina às {consulta_fim.strftime("%H:%M")}). '
                        f'A consulta tem duração de {self.CONSULTATION_DURATION} minutos.'
                    )
                })

        conflitos_paciente = base_qs.filter(patient=data['patient'])

        if self.instance:
            conflitos_paciente = conflitos_paciente.exclude(pk=self.instance.pk)

        for consulta in conflitos_paciente:
            if self._check_time_overlap(data['time'], consulta.time):
                consulta_datetime = datetime.combine(datetime.today(), consulta.time)
                consulta_fim = (consulta_datetime + timedelta(minutes=self.CONSULTATION_DURATION)).time()

                print(consulta)
                raise serializers.ValidationError({
                    'time': (
                        f'Conflito de horário! O paciente já tem uma consulta às {consulta.time.strftime("%H:%M")} '
                        f'(termina às {consulta_fim.strftime("%H:%M")}). '
                        f'A consulta tem duração de {self.CONSULTATION_DURATION} minutos.'
                    )
                })

        return data


class AppointmentListSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    recurrence_type = HealthPlanSerializer(read_only=True)
    end_time = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'patient', 'date', 'time', 'end_time', 'recurrence_type', 'is_active', 'created_at']
        read_only_fields = fields

    def get_end_time(self, obj):
        consultation_datetime = datetime.combine(datetime.today(), obj.time)
        end_datetime = consultation_datetime + timedelta(minutes=40)
        return end_datetime.time().strftime("%H:%M")
