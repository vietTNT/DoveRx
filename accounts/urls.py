from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    DoctorRegisterView,
    VerifyOTPView,
    ProfileAPIView,
    UpdateProfileAPIView,
    CustomLoginView,
)
from .views_google import GoogleLoginAPIView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register/doctor/", DoctorRegisterView.as_view(), name="register-doctor"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("google-login/", GoogleLoginAPIView.as_view(), name="google-login"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path("update-profile/", UpdateProfileAPIView.as_view(), name="update-profile"),
]
