from uuid import uuid4

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from elections.models import Election, Voter, Option


class ElectionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    votable = serializers.IntegerField(min_value=1, required=False)

    def create(self, validated_data):
        # use value from the received data or the default values
        votable = 1
        if 'votable' in validated_data:
            votable = validated_data.get('votable')
        description = ''
        if 'description' in validated_data:
            description = validated_data.get('description')

        # create the election with the received data
        return Election.objects.create(
            name=validated_data.get('name'),
            description=description,
            votable=votable,
            owner=validated_data.get('user')
        )

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        # update only if params available in the payload data
        if 'votable' in validated_data:
            instance.votable = validated_data.get('votable')
        if 'description' in validated_data:
            instance.description = validated_data.get('description')
        # save the updated instance
        instance.save()
        return instance

    def to_representation(self, instance):
        # return elections information
        ret = {
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "paused": False,
            "voters": instance.voters,
            "voted": instance.voted,
            "creation_date": instance.creation_date,
            "start_date": instance.start_date,
            "end_date": instance.end_date
        }
        # correct value if election is currently paused
        if instance.paused == 1:
            ret["paused"] = True
        return ret


class ElectionDetailSerializer(ElectionSerializer):

    def to_representation(self, instance):
        # call standard election to representation function
        ret = ElectionSerializer.to_representation(self, instance)
        # add more detailed information
        ret["votable"] = instance.votable
        ret["options"] = []
        ret["voters"] = []

        # add all options and voters of this election
        for option in Option.objects.filter(election_id=instance.id).values():
            ret["options"].append(option.get('name'))
        for voter in Voter.objects.filter(election_id=instance.id).values():
            ret["voters"].append(voter.get('email'))
        return ret


class OptionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)

    def create(self, validated_data):
        election_id = validated_data.get('election_id')
        name = validated_data.get('name')
        # check if option name already existing for this election
        if Option.objects.filter(election_id=election_id, name=name).exists():
            # option name already existing
            raise ValidationError({"detail": "duplicate entry"})
        return Option.objects.create(
            name=name,
            election_id=election_id
        )

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        # update only if there is a difference
        if instance.name != name:
            # check if option name already existing for this election
            if Option.objects.filter(election_id=instance.election_id,
                                     name=name).exists():
                # option name already existing
                raise ValidationError({"detail": "duplicate entry"})
            instance.name = name
            instance.save()
        return instance


class VoterSerializer(serializers.Serializer):
    voters = serializers.ListField(
        child=serializers.CharField(max_length=255)
    )


class VoterDetailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    def __generate_token(self, election_id):
        token = str(uuid4())
        return (token[:10] + hex(election_id)[2:] + token[10:]).upper()

    def create(self, validated_data):
        email = validated_data.get('email')
        election_id = validated_data.get('election_id')

        if Voter.objects.filter(election_id=election_id, email=email).exists():
            # voter for this election already existing
            raise ValidationError()

        # generate token
        token = self.__generate_token(election_id)
        while Voter.objects.filter(token=token).exists():
            # repeat while duplicate exists
            token = self.__generate_token(election_id)

        return Voter.objects.create(
            token=token,
            email=email,
            election_id=election_id
        )


class VoteSerializer(serializers.Serializer):
    votes = serializers.ListField(
        child=serializers.IntegerField(min_value=0)
    )

    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('options')
        self.votable = kwargs.pop('votable')
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        # remove duplicates
        attrs['votes'] = list(set(attrs.get('votes')))
        # check if there are too many voted options
        if len(attrs.get('votes')) > self.votable:
            raise ValidationError('Too many options')
        # check if every option is in the range of the available options
        for vote in attrs.get('votes'):
            if vote >= self.options:
                raise ValidationError('Out of range')
        return attrs