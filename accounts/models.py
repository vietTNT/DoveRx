from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid
import random
import datetime

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('user', 'User'),
    ]

    GENDER_CHOICES = [
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác'),
    ]

    DOCTOR_TYPE_CHOICES = [
        ('doctor', 'Bác sĩ chính thức'),
        ('student', 'Sinh viên y khoa'),
        ('intern', 'Thực tập sinh'),
    ]

    # --- Thông tin tài khoản ---
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_verified = models.BooleanField(default=False)

    # --- Thông tin cá nhân ---
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    # --- Thông tin nghề nghiệp (chỉ áp dụng với bác sĩ) ---
    specialty = models.CharField(max_length=100, blank=True, null=True)
    workplace = models.CharField(max_length=150, blank=True, null=True)
    experience_years = models.PositiveIntegerField(blank=True, null=True)
    license_number = models.CharField(
        max_length=100, blank=True, null=True, help_text="Số chứng chỉ hành nghề"
    )
    doctor_type = models.CharField(
        max_length=50, choices=DOCTOR_TYPE_CHOICES, blank=True, null=True
    )

    # --- Xác minh OTP ---
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    def generate_otp(self):
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
        self.save()
