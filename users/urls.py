from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("list/", views.participant_list, name="list"),
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("<int:pk>/", views.user_detail, name="detail"),
]
