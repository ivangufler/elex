from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from elections.models import Election, Voter, Option


class ElectionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    votable = serializers.IntegerField(min_value=1, required=False)

    def create(self, validated_data):
        votable = 1
        if 'votable' in validated_data:
            votable = validated_data.get('votable')
        description = ''
        if 'description' in validated_data:
            description = validated_data.get('description')

        return Election.objects.create(
            name=validated_data.get('name'),
            description=description,
            votable=votable,
            owner=validated_data.get('user')
        )

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        if 'votable' in validated_data:
            instance.votable = validated_data.get('votable')
        if 'description' in validated_data:
            instance.description = validated_data.get('description')
        instance.save()
        return instance

    def to_representation(self, instance):
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
        if instance.paused == 1:
            ret["paused"] = True
        return ret


class ElectionDetailSerializer(ElectionSerializer):

    def to_representation(self, instance):
        ret = ElectionSerializer.to_representation(self, instance)
        ret["votable"] = instance.votable
        ret["options"] = []
        ret["voters"] = []

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

        if Option.objects.filter(election_id=election_id, name=name).exists():
            raise ValidationError({"detail": "duplicate entry"})
        return Option.objects.create(
            name=name,
            election_id=election_id
        )

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        if instance.name != name:
            if Option.objects.filter(election_id=instance.election_id,
                                     name=name).exists():
                raise ValidationError({"detail": "duplicate entry"})
            instance.name = name
            instance.save()
        return instance