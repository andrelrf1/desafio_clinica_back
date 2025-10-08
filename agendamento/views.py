from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, Doctor, HealthPlan, Patient, Appointment
from .serializers import (
    UserSerializer,
    UserLoginSerializer,
    DoctorSerializer,
    HealthPlanSerializer,
    PatientSerializer,
    AppointmentSerializer,
    AppointmentListSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {'error': 'Email e senha são obrigatórios.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=email, password=password)

    if user is not None:
        if not user.is_active:
            return Response(
                {'error': 'Usuário inativo.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Login realizado com sucesso!',
            'user': UserLoginSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

    return Response(
        {'error': 'Email ou senha inválidos.'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response(
            {'message': 'Logout realizado com sucesso.'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': 'Token inválido ou já expirado.'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    serializer = UserLoginSerializer(request.user)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_appointment(request, appointment_id):
    try:
        appointment = Appointment.objects.select_related('patient', 'patient__user').get(
            id=appointment_id, is_active=True
        )
    except Appointment.DoesNotExist:
        return Response(
            {"detail": "Agendamento não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if getattr(appointment.patient, 'user_id', None) != request.user.id:
        return Response(
            {"detail": "Você não tem permissão para cancelar este agendamento."},
            status=status.HTTP_403_FORBIDDEN,
        )

    appointment.is_active = False
    appointment.save()
    return Response(
        {"message": "Agendamento cancelado com sucesso."},
        status=status.HTTP_204_NO_CONTENT,
    )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'user_pk'

    @action(detail=True, methods=['get'], url_path='patient')
    def patient(self, request, user_pk=None):
        try:
            patient = Patient.objects.select_related('user', 'health_plan').get(
                user_id=user_pk, is_active=True
            )
        except Patient.DoesNotExist:
            return Response(
                {"detail": "Paciente não encontrado para este usuário."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PatientSerializer(patient)
        return Response(serializer.data)


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Doctor.objects.filter(is_active=True)
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'doctors_pk'

    @action(detail=True, methods=['get'], url_path='appointments')
    def appointments(self, request, doctors_pk=None):
        if not Doctor.objects.filter(id=doctors_pk, is_active=True).exists():
            return Response(
                {"detail": "Médico não encontrado ou inativo."},
                status=status.HTTP_404_NOT_FOUND,
            )

        appointments = AppointmentViewSet.queryset.filter(doctor_id=doctors_pk)
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)


class HealthPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HealthPlan.objects.filter(is_active=True)
    serializer_class = HealthPlanSerializer
    permission_classes = [IsAuthenticated]


class PatientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Patient.objects.filter(is_active=True).select_related('user', 'health_plan')
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'patient_pk'

    @action(detail=True, methods=['get'], url_path='appointments')
    def appointments(self, request, patient_pk=None):
        if not Patient.objects.filter(id=patient_pk, is_active=True).exists():
            return Response(
                {"detail": "Paciente não encontrado ou inativo."},
                status=status.HTTP_404_NOT_FOUND,
            )

        appointments = AppointmentViewSet.queryset.filter(patient_id=patient_pk)
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.filter(is_active=True).select_related(
        'doctor', 'patient', 'patient__user', 'patient__health_plan', 'recurrence_type'
    ).order_by('-date', '-time')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return AppointmentListSerializer
        return AppointmentSerializer

    def destroy(self, request, *args, **kwargs):
        appointment = self.get_object()
        appointment.is_active = False
        appointment.save()
        return Response(
            {'message': 'Agendamento cancelado com sucesso.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'], url_path='by-doctor')
    def by_doctor(self, request):
        doctor_id = request.query_params.get('doctor_id')
        if not doctor_id:
            return Response(
                {'error': 'doctor_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointments = self.queryset.filter(doctor_id=doctor_id)
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-patient')
    def by_patient(self, request):
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointments = self.queryset.filter(patient_id=patient_id)
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-date')
    def by_date(self, request):
        date = request.query_params.get('date')
        if not date:
            return Response(
                {'error': 'date é obrigatório (formato: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointments = self.queryset.filter(date=date)
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-date-range')
    def by_date_range(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response(
                {'error': 'start_date e end_date são obrigatórios (formato: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointments = self.queryset.filter(date__range=[start_date, end_date])
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)
