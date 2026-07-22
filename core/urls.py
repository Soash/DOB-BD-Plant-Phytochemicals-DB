from django.urls import path
from . import views

urlpatterns = [
    path('', views.bmppd, name='bmppd'),
    path('bmppd_result/', views.bmppd_result, name='bmppd_result'),
    path('about/', views.about, name='about'),
    path('acknowledgement/', views.acknowledgement, name='acknowledgement'),
    path("reference/", views.reference, name="reference"),
    path('request-plant/', views.request_plant, name='request_plant'),
    path('manage-requests/', views.manage_requests, name='manage_requests'),
    path('manage-requests/<int:pk>/notify/', views.notify_plant_request, name='notify_plant_request'),
    path('manage-requests/<int:pk>/edit/', views.edit_plant_request, name='edit_plant_request'),
    path('manage-requests/<int:pk>/delete/', views.delete_plant_request, name='delete_plant_request'),
]
