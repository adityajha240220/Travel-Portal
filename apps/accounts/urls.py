from django.urls import path
from .views import (
    LoginPageView,
    HomePageView,
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView
)

urlpatterns = [
    # Frontend HTML views (CBVs)
    path('login-page/', LoginPageView.as_view(), name='login-page'),
    path('home-page/', HomePageView.as_view(), name='home-page'),

    # API endpoints (CBVs)
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
