from django.urls import path

from . import views

urlpatterns = [
    path('vote/<str:token>', views.VoteView.as_view()),
    path('user', views.UserView.as_view()),
    path('election', views.ElectionList.as_view()),
    path('election/<int:election_id>', views.ElectionDetail.as_view()),
    path('election/<int:election_id>/start', views.StartElection.as_view()),
    path('election/<int:election_id>/end', views.EndElection.as_view()),
    path('election/<int:election_id>/pause', views.PauseElection.as_view()),
    path('election/<int:election_id>/remind', views.VoteReminder.as_view()),
    path('election/<int:election_id>/results', views.PDFResults.as_view()),
    path('election/<int:election_id>/voter', views.VoterList.as_view()),
    path('election/<int:election_id>/voter/<str:email>', views.VoterDetail.as_view()),
    path('election/<int:election_id>/option', views.OptionList.as_view()),
    path('election/<int:election_id>/option/<int:index>', views.OptionDetail.as_view()),
]