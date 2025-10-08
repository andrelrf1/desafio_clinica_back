from rest_framework.routers import DefaultRouter
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from agendamento.views import (
    login_view,
    logout_view,
    me_view,
    UserViewSet,
    DoctorViewSet,
    HealthPlanViewSet,
    PatientViewSet,
    AppointmentViewSet,
    delete_appointment,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'health-plans', HealthPlanViewSet, basename='healthplan')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/me/', me_view, name='me'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('appointment/<int:appointment_id>/', delete_appointment, name='delete_appointment'),
    path('', include(router.urls))
]
