"""URL routes for the accounts app: register, login, logout, password."""

from django.urls import path

from accounts.admin_views import AdminUserDetailView, AdminUserListView, ChangePasswordView
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
    path("password/", ChangePasswordView.as_view(), name="change-password"),
    path("users/", UserListView.as_view(), name="users"),
    path("users/<int:user_id>/", UserRoleView.as_view(), name="user-role"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user"),
]
