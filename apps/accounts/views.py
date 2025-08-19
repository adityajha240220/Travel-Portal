from django.views import View
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny # <--- Import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import CustomUser
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

# Class-based View for rendering login.html
class LoginPageView(View):
    def get(self, request):
        return render(request, 'accounts/login.html')


# Optional Home Page View (not used if login.html is the main dashboard)
class HomePageView(View):
    def get(self, request):
        return render(request, 'home.html')


class RegisterView(APIView):
    permission_classes = [AllowAny] # <--- ADD THIS LINE
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny] # <--- ADD THIS LINE
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data
                })
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated] # This is correct, only authenticated users can log out

    def post(self, request):
        # Ensure the user has an auth token before trying to delete it
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
            return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'No active token found for this user.'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated] # This is correct, only authenticated users can view profile

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)