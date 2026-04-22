from django.urls import path
from .views import *

urlpatterns = [
    # Paths /users/
    path('login', login_view, name='login'),
    path('logout', logout_view, name='logout'),
    path('register', register_view, name='register'),
    path('profile', profile_view, name='profile'),
    path('edit_profile', edit_profile_view, name='edit_profile'),
]