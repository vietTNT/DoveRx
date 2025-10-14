
import requests
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.permissions import AllowAny

class GoogleLoginAPIView(APIView):
    """
    API xác thực đăng nhập bằng Google OAuth2 từ frontend (React)
    """
    permission_classes = [AllowAny]  #
    def post(self, request):
        # React gửi id_token (credential từ Google)
        id_token = request.data.get("id_token")

        if not id_token:
            print("❌ Thiếu id_token trong request:", request.data)
            return Response(
                {"error": "Missing id_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        print("🟢 Nhận id_token từ frontend:", id_token[:50], "...")

        # Xác minh id_token với Google
        google_response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        )

        print("🔵 Phản hồi từ Google:", google_response.status_code)
        print("🟣 Nội dung:", google_response.text[:200], "\n")

        if google_response.status_code != 200:
            return Response(
                {
                    "error": "Invalid Google token",
                    "google_response": google_response.text,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Dữ liệu người dùng trả về từ Google
        user_data = google_response.json()
        email = user_data.get("email")
        name = user_data.get("name")

        if not email:
            return Response(
                {"error": "Google account has no email"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Tạo hoặc lấy user ---
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": name.split(" ")[0] if name else "",
                "last_name": " ".join(name.split(" ")[1:]) if name and len(name.split(" ")) > 1 else "",
                "role": "user",  # mặc định người dùng bình thường
            },
        )

        if created:
            print(f"🆕 Tạo user mới: {user.username} ({user.email})")
        else:
            print(f"✅ Đăng nhập lại: {user.username} ({user.email})")

        # --- Cấp JWT token ---
        refresh = RefreshToken.for_user(user)

        # --- Chuẩn hóa dữ liệu trả về cho frontend ---
        user_info = {
            "id": user.id,
            "email": user.email,
            "name": user.get_full_name() or user.username,
            "role": user.role,
            "avatar": request.build_absolute_uri(user.avatar.url) if user.avatar else None,
            "bio": user.bio,
            "specialty": user.specialty,
            "workplace": user.workplace,
            "experience_years": user.experience_years,
            "phone": user.phone,
        }

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": user_info,
            },
            status=status.HTTP_200_OK,
        )
