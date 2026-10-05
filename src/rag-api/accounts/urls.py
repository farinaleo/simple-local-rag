"""URL routes for the accounts app: register, login, logout, roles."""

from django.urls import path

from accounts.views import (
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    UserListView,
    UserRoleView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("users/", UserListView.as_view(), name="users"),
    path("users/<int:user_id>/", UserRoleView.as_view(), name="user-role"),
]
