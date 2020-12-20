from django.http import Http404
from django.shortcuts import render
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from elections.models import Election
from elections.serializers import *


# Create your views here.
class ElectionAPI(APIView):
    def get_election(self, election_id, user):
        try:
            election = Election.objects.get(id=election_id)
            if election.owner != user:
                return None
            return election
        except Election.DoesNotExist:
            raise Http404

    def get_state(self, id):
        election = self.get_election(id)
        if election.paused == 1:
            # election is paused
            return -1
        if election.start_date is None:
            # election was created
            return 0
        if election.end_date is None:
            # election is in progress
            return 1
        # election is closed
        return 2


class VoteView(ElectionAPI):
    def get(self, request, token):
        pass

    def post(self, request, token):
        pass


class ElectionList(ElectionAPI):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        elections = Election.objects.all().filter(owner=request.user)
        serializer = ElectionSerializer(elections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = ElectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ElectionDetail(ElectionAPI):
    def get(self, request, election_id):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        election = self.get_election(election_id, request.user)
        if election is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = ElectionDetailSerializer(election)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, election_id):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        election = self.get_election(election_id, request.user)
        if election is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = ElectionDetailSerializer(election, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        if (not request.user.is_authenticated) or \
                self.get_election(election_id, request.user) is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = OptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(election_id=election_id)
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OptionDetail(ElectionAPI):
    def get_option(self, election_id, index):
        try:
            return Option.objects.filter(election_id=election_id)[index]
        except IndexError:
            raise Http404

    def put(self, request, election_id, index):
        if (not request.user.is_authenticated) or \
                self.get_election(election_id, request.user) is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        option = self.get_option(election_id, index)
        serializer = OptionSerializer(option, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoterList(ElectionAPI):
    def post(self, request, election_id):
        pass


class VoterDetail(ElectionAPI):
    def delete(self, request, election_id, email):
        pass