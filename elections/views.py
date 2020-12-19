from django.shortcuts import render
from rest_framework.views import APIView


# Create your views here.
class ElectionAPI(APIView):
    def get_election(self, election_id):
        pass


class VoteView(ElectionAPI):
    def get(self, request, token):
        pass

    def post(self, request, token):
        pass


class ElectionList(ElectionAPI):
    def get(self, request):
        pass

    def post(self, request):
        pass


class ElectionDetail(ElectionAPI):
    def get(self, request, election_id):
        pass

    def put(self, request, election_id):
        pass


class StartElection(ElectionAPI):
    def post(self, request, election_id):
        pass


class EndElection(ElectionAPI):
    def post(self, request, election_id):
        pass


class PauseElection(ElectionAPI):
    def post(self, request, election_id):
        pass


class VoteReminder(ElectionAPI):
    def post(self, request, election_id):
        pass


class OptionList(ElectionAPI):
    def post(self, request, election_id):
        pass


class OptionDetail(ElectionAPI):
    def put(self, request, election_id, index):
        pass


class VoterList(ElectionAPI):
    def post(self, request, election_id):
        pass


class VoterDetail(ElectionAPI):
    def delete(self, request, election_id, email):
        pass