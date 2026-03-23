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

        """if data["stream"]:
            data['stream'] = "http://127.0.0.1:8000" + reverse('stream', kwargs={'pk': instance.id})"""
        # https://cfnd.cinemap.cc/1774311867-UuQKEwuxFGuqclEDGnQqkEugbOBOlRb%2BAkgLsD4a9Ic%3D/tvseries/66e18d23cc4462f1022af6fe720251b3ea977be1/d2cf39f82e33728d6eba8679add0dc90:2026032400/hls.m3u8
        # https://cfnd.cinemap.cc/1774202858-9YdegEM7QaSwzzG36%2BsCWpRoSnEMfz3uHm%2BZz5eOAn8%3D/tvseries/5ed1005ca4e77f372093f54db7b0f2d25f2c6bfb/c47a972eb4c6282d4c6ac5f7634ca795:2026032218/hls-v1-a2.m3u8
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
