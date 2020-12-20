from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
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
                # return None if user does not own this election
                return None
            return election
        except Election.DoesNotExist:
            raise Http404

    def get_state(self, election_id):
        try:
            election = Election.objects.get(id=election_id)
        except Election.DoesNotExist:
            raise Http404
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
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # get all elections of the loggedin user and return them
        elections = Election.objects.all().filter(owner=request.user)
        serializer = ElectionSerializer(elections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # create new election from received payload
        serializer = ElectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ElectionDetail(ElectionAPI):
    def get(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = ElectionDetailSerializer(election)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # changing election only possible when it has not started yet
        if self.get_state(election_id) == 0:
            # update the election with the received payload
            serializer = ElectionDetailSerializer(election, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_403_FORBIDDEN)


class StartElection(ElectionAPI):
    def post(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        number_of_options = Option.objects.filter(election_id=election_id).count()
        # starting election only possible when it has not started yet and when there is at least one
        # voter and two vote options
        if self.get_state(election_id) == 0 and election.voters >= 1 and number_of_options >= 2:
            election.start_date = timezone.now()
            election.save()
            # TODO send emails
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class EndElection(ElectionAPI):
    def post(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # ending election only possible when it is in progress
        if abs(self.get_state(election_id)) == 1:
            election.end_date = timezone.now()
            election.paused = 0
            election.save()
            Voter.objects.filter(election_id=election_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class PauseElection(ElectionAPI):
    def post(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # pausing election only possible when it is in progress
        if abs(self.get_state(election_id)) == 1:
            election.paused = (election.paused - 1) * (-1)
            election.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class VoteReminder(ElectionAPI):
    def post(self, request, election_id):
        pass


class OptionList(ElectionAPI):
    def post(self, request, election_id):
        if (not request.user.is_authenticated) or \
                self.get_election(election_id, request.user) is None:
            # user is not logged in or does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # creating options is only possible when election not has started yet
        if self.get_state(election_id) == 0:
            # create a new election with data from the payload
            serializer = OptionSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(election_id=election_id)
                return Response(status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_403_FORBIDDEN)


class OptionDetail(ElectionAPI):
    def get_option(self, election_id, index):
        try:
            # return the option at index for the requested election
            return Option.objects.filter(election_id=election_id)[index]
        except IndexError:
            # if index to big option was not found (because not existing)
            raise Http404

    def put(self, request, election_id, index):
        if (not request.user.is_authenticated) or \
                self.get_election(election_id, request.user) is None:
            # user is not logged in or does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # updating options is only possible when election not has started yet
        if self.get_state(election_id) == 0:
            # get the requested option and update it with data in payload
            option = self.get_option(election_id, index)
            serializer = OptionSerializer(option, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, election_id, index):
        if (not request.user.is_authenticated) or \
                self.get_election(election_id, request.user) is None:
            # user is not logged in or does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # deleting options is only possible when election not has started yet
        if self.get_state(election_id) == 0:
            # get the requested option and delete it
            option = self.get_option(election_id, index)
            option.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class VoterList(ElectionAPI):
    def post(self, request, election_id):
        if not request.user.is_authenticatede:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        election = self.get_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        state = self.get_state(election_id)
        # add voters as long as election not ended
        if state == 2:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = VoterSerializer(data=request.data)
        # correct list of values
        if serializer.is_valid():
            fails = {}
            voters = request.data.get('voters')
            # for each email in the voters list
            for voter in voters:
                # check if email is valid
                serializer = VoterDetailSerializer(data={"email": voter})
                if serializer.is_valid():
                    # save new voter
                    try:
                        serializer.save(election_id=election_id)
                        election.voters = election.voters + 1
                        election.save()
                        # if election already in progress, send vote link immediately
                        if abs(state) == 1:
                            # TODO send emails
                            pass
                    # email already existing for this election
                    except ValidationError:
                        # add email to failed entries
                        fails[voter] = ["duplicate entry"]
                else:
                    # email not valid, add to failed entries
                    fails[voter] = serializer.errors["email"]
            # return failed entries
            return Response(fails, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoterDetail(ElectionAPI):
    def get_voter(self, election_id, email):
        # try to get election, http404 if it does not exist
        try:
            Election.objects.get(id=election_id)
        except Election.DoesNotExist:
            raise Http404
        # get voter for requested election and email, http4 if not existing
        try:
            return Voter.objects.filter(election_id=election_id).get(email=email)
        except Voter.DoesNotExist:
            raise Http404

    def delete(self, request, election_id, email):
        if (not request.user.is_authenticated) or \
                self.get_election(election_id, request.user) is None:
            # user is not logged in or does not own the requested election
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # delete voters as long as election has not ended
        if self.get_state(election_id) == 0:
            # get requested voter and delete it
            voter = self.get_voter(election_id, email)
            voter.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)
