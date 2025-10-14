from django.shortcuts import render
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import RegisterSerializer, UserSerializer
from django.core.mail import send_mail
from django.conf import settings
import random
import datetime
from django.utils import timezone
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .serializers import CustomTokenObtainPairSerializer

User = get_user_model()


# 🟢 Đăng ký người dùng
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


# 🟢 Lấy thông tin hồ sơ người dùng hiện tại
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# 🟡 Cập nhật thông tin hồ sơ
# class UpdateProfileAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def put(self, request):
#         user = request.user
#         serializer = UserSerializer(user, data=request.data, partial=True)

#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# class UpdateProfileAPIView(generics.UpdateAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]

#     def get_object(self):
#         return self.request.user

#     def put(self, request, *args, **kwargs):
#         user = self.get_object()
#         serializer = self.get_serializer(user, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         print("❌ Serializer errors:", serializer.errors)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     def create(self, request, *args, **kwargs):
#         data = request.data.copy()
#         data["role"] = "doctor"  # ✅ mặc định là bác sĩ

#         serializer = self.get_serializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()

#         return Response(
#             {
#                 "message": "Tài khoản bác sĩ được tạo thành công.",
#                 "user": serializer.data,
#             },
#             status=status.HTTP_201_CREATED,
#         )
from rest_framework.parsers import MultiPartParser, FormParser
class UpdateProfileAPIView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 
    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # trả về với context để build absolute avatar URL
            return Response(UserSerializer(user, context={"request": request}).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        print("📩 Dữ liệu nhận từ frontend:", data)

        try:
            print("👉 BẮT ĐẦU KIỂM TRA EMAIL / USERNAME / PASSWORD")
            email = data.get("email")
            username = data.get("username")
            password = data.get("password")

            if not email or not username or not password:
                print("❌ Thiếu thông tin cơ bản")
                return Response({"error": "Thiếu email, tên đăng nhập hoặc mật khẩu."},
                                status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email=email).exists():
                print("❌ Email đã tồn tại:", email)
                return Response( {"error": "Email đã tồn tại trong hệ thống."},
                                status=status.HTTP_400_BAD_REQUEST,)

            print("✅ Tạo user...")
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                role="doctor",
                doctor_type=data.get("doctorType"),
                specialty=data.get("specialty", ""),
                workplace=data.get("workplace", ""),
                phone=data.get("phone", ""),
                license_number=data.get("license_number", ""),
            )
            print("✅ USER ĐÃ TẠO:", user)

            print("🔹 Tạo mã OTP...")
            user.generate_otp()
            print("✅ OTP:", user.otp_code)

            print("✉️ Gửi mail tới:", user.email)
            send_mail(
                subject="🔐 Mã xác nhận tài khoản DoveRx của bạn",
                message=f"Xin chào {user.first_name or user.username},\n\n"
                        f"Mã xác nhận của bạn là: {user.otp_code}\n"
                        f"Mã có hiệu lực trong 10 phút.\n\nCảm ơn bạn đã đăng ký DoveRx!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            print("✅ MAIL ĐÃ GỬI THÀNH CÔNG!")
            return Response({"message": "Đăng ký thành công! Vui lòng kiểm tra email để xác minh tài khoản."},
                            status=status.HTTP_201_CREATED)

        except Exception as e:
            import traceback
            print("❌ Lỗi khi đăng ký bác sĩ:", e)
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        try:
            user = User.objects.get(email=email)

            if not user.otp_code:
                return Response({"error": "Tài khoản chưa yêu cầu OTP."}, status=status.HTTP_400_BAD_REQUEST)

            if user.otp_code != otp:
                return Response({"error": "Mã xác nhận không đúng."}, status=status.HTTP_400_BAD_REQUEST)

            if timezone.now() > user.otp_expiry:
                return Response({"error": "Mã xác nhận đã hết hạn."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Nếu hợp lệ
            user.is_verified = True
            user.otp_code = None
            user.save()

            return Response({"message": "Xác minh thành công! Tài khoản đã được kích hoạt."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "Không tìm thấy tài khoản này."}, status=status.HTTP_404_NOT_FOUND)

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

