from django.urls import path, include

from . import views

urlpatterns = [
    path('',  views.loginView, name="stock-login"),
    path('signup/', views.signupView, name='stock-signup'),
    path('logout/',  views.logoutView, name="stock-logout"),
    path('picker/', views.stockPickerView, name="stock-picker"),
    path('live/', views.stockTrackerView, name="stock-tracker"),
]