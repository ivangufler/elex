from django.urls import path

from . import views

urlpatterns = [
    path('election', views.ElectionList.as_view()),
    path('election/<int:election_id>', views.ElectionDetail.as_view()),
]