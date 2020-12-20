from django.http import Http404
from django.template.loader import get_template
from django.utils import timezone
from django.core.mail import get_connection, EmailMultiAlternatives
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from elections.serializers import *


def send_emails(voters, election, reminder=False):
    subject = 'Wahl: ' + election.name
    if reminder:
        subject = 'Erinnerung - ' + subject
    connection = get_connection(fail_silently=False)
    messages = []

    for voter in voters:
        msg = EmailMultiAlternatives(
            subject=subject,
            body='',
            to=[voter.email],
            reply_to=[election.owner.email]
        )
        context = {"election_name": election.name, "token": voter.token}
        msg.attach_alternative(get_template('new.html').render(context), 'text/html')
        messages.append(msg)
    return connection.send_messages(messages)


class ElectionAPI(APIView):

    def get_election(self, election_id):
        try:
            return Election.objects.get(id=election_id)
        except Election.DoesNotExist:
            raise Http404

    def get_admin_election(self, election_id, user):
        election = self.get_election(election_id)
        if election.owner != user:
            # return None if user does not own this election
            return None
        return election

    def get_option(self, election_id, index):
        try:
            # return the option at index for the requested election
            return Option.objects.filter(election_id=election_id)[index]
        except IndexError:
            # if index to big option was not found (because not existing)
            raise Http404

    def get_state(self, election_id):
        election = self.get_election(election_id)
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
    def get_voter(self, token):
        try:
            voter = Voter.objects.get(token=token)
            election = self.get_election(voter.election_id)
            return voter, election
        except Voter.DoesNotExist:
            raise Http404

    def get(self, request, token):
        voter, election = self.get_voter(token)
        # only if election is in progress and voter has not voted yet, voting is allowed
        if self.get_state(election.id) != 1 or voter.voted == 1:
            return Response(status=status.HTTP_403_FORBIDDEN)

        ret = {
            "name": election.name,
            "description": election.description,
            "owner": election.owner.first_name + ' ' + election.owner.last_name,
            "votable": election.votable,
            "options": []
        }

        for option in Option.objects.filter(election_id=election.id).values():
            ret["options"].append(option.get('name'))
        return Response(ret, status=status.HTTP_200_OK)

    def post(self, request, token):
        voter, election = self.get_voter(token)
        # only if election is in progress and voter has not voted yet, voting is allowed
        if self.get_state(election.id) != 1 or voter.voted == 1:
            return Response(status=status.HTTP_403_FORBIDDEN)
        # get all available options for this election
        options = Option.objects.filter(election_id=election.id).count()
        serializer = VoteSerializer(data=request.data, options=options, votable=election.votable)
        # if all the provided votes are valid
        if serializer.is_valid():
            for vote in serializer.data.get('votes'):
                option = self.get_option(election.id, vote)
                # increase votes for voted option
                option.votes = option.votes + 1
                option.save()
            # increase total number of people who voted
            election.voted = election.voted + 1
            election.save()
            # voter has just voted, set voted to true (1)
            voter.voted = 1
            voter.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        election = self.get_admin_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = ElectionDetailSerializer(election)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_admin_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
        # changing election only possible when it has not started yet
        if self.get_state(election.id) == 0:
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
        election = self.get_admin_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
        number_of_options = Option.objects.filter(election_id=election.id).count()
        # starting election only possible when it has not started yet and when there is at least one
        # voter and two vote options
        if self.get_state(election.id) == 0 and election.voters >= 1 and number_of_options >= 2:
            election.start_date = timezone.now()
            election.save()
            send_emails(Voter.objects.filter(election_id=election.id), election)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class EndElection(ElectionAPI):
    def post(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_admin_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
        # ending election only possible when it is in progress
        if abs(self.get_state(election.id)) == 1:
            election.end_date = timezone.now()
            election.paused = 0
            election.save()
            Voter.objects.filter(election_id=election.id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class PauseElection(ElectionAPI):
    def post(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_admin_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
        # pausing election only possible when it is in progress
        if abs(self.get_state(election.id)) == 1:
            election.paused = (election.paused - 1) * (-1)
            election.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class VoteReminder(ElectionAPI):
    def post(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_admin_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
        # sending remind emails only possible while election in progress/paused
        if abs(self.get_state(election.id)) == 1:
            send_emails(Voter.objects.filter(election_id=election.id, voted=0), election, True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class PDFResults(ElectionAPI):
    def get(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # get the requested election and return it
        election = self.get_admin_election(election_id, request.user)
        if election is None:
            # logged in user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
        # results only available if election already ended
        if self.get_state(election.id) == 2:
            # TODO generate results PDF
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)


class OptionList(ElectionAPI):
    def post(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if self.get_admin_election(election_id, request.user) is None:
            # user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
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
    def put(self, request, election_id, index):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if self.get_admin_election(election_id, request.user) is None:
            # user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
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
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if self.get_admin_election(election_id, request.user) is None:
            # user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)
        # deleting options is only possible when election not has started yet
        if self.get_state(election_id) == 0:
            # get the requested option and delete it
            option = self.get_option(election_id, index)
            option.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class VoterList(ElectionAPI):
    def post(self, request, election_id):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        election = self.get_admin_election(election_id, request.user)
        if election is None:
            # user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)

        state = self.get_state(election.id)
        # add voters as long as election not ended
        if state == 2:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = VoterSerializer(data=request.data)
        # correct list of values
        if serializer.is_valid():
            fails = {}
            new_voters = []
            voters = request.data.get('voters')
            # for each email in the voters list
            for voter in voters:
                # check if email is valid
                serializer = VoterDetailSerializer(data={"email": voter})
                if serializer.is_valid():
                    # save new voter
                    try:
                        # if election already in progress, we need to send later the links
                        if abs(state) == 1:
                            new_voters.append(Voter.objects.get(election_id=election.id,
                                                                email=serializer.data.get('email')))
                        serializer.save(election_id=election.id)
                        election.voters = election.voters + 1
                        election.save()
                    # email already existing for this election
                    except ValidationError:
                        # add email to failed entries
                        fails[voter] = ["duplicate entry"]
                else:
                    # email not valid, add to failed entries
                    fails[voter] = serializer.errors["email"]

            # if election already in progress, send the links
            if abs(state) == 1:
                send_emails(new_voters, election)
                pass
            # return failed entries
            return Response(fails, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoterDetail(ElectionAPI):
    def get_voter(self, election_id, email):
        # try to get election, http404 if it does not exist
        self.get_election(election_id)
        # get voter for requested election and email, http4 if not existing
        try:
            return Voter.objects.filter(election_id=election_id).get(email=email)
        except Voter.DoesNotExist:
            raise Http404

    def delete(self, request, election_id, email):
        if not request.user.is_authenticated:
            # user is not logged in
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if self.get_admin_election(election_id, request.user) is None:
            # user does not own the requested election
            return Response(status=status.HTTP_403_FORBIDDEN)

        # delete voters as long as election has not ended
        if self.get_state(election_id) == 0:
            # get requested voter and delete it
            voter = self.get_voter(election_id, email)
            voter.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)
