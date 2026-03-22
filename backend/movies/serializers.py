from rest_framework import serializers
from django.urls import reverse

from .models import Source, Movie, History, MovieEpisode, Translation


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=True, max_length=100)
    source = serializers.ListField(
        child=serializers.ChoiceField(choices=Source),
        required=True
    )


class TranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translation
        fields = '__all__'


class MovieEpisodeSerializer(serializers.ModelSerializer):
    translation = TranslationSerializer(read_only=True)

    class Meta:
        model = MovieEpisode
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if data["stream"]:
            data['stream'] = "http://127.0.0.1:8000" + reverse('stream', kwargs={'pk': instance.id})

        return data


class MovieSerializer(serializers.ModelSerializer):
    episodes = MovieEpisodeSerializer(read_only=True, many=True)

    class Meta:
        model = Movie
        fields = '__all__'


class HistorySerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = History
        fields = '__all__'
