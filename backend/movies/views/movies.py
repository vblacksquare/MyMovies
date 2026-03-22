
import m3u8
import requests
import logging
import base64

from asgiref.sync import async_to_sync
from django.http import Http404
from django.utils import timezone
from django.urls import reverse
from django.http import StreamingHttpResponse, HttpResponse

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import SearchSerializer, MovieSerializer, MovieEpisode, Translation, MovieEpisodeSerializer
from ..models import Movie, History, Socket
from .parser import search, fill, fill_episode


logger = logging.getLogger("movies")


class SearchView(APIView):
    def get(self, request: Request):
        serializer = SearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data["query"]
        source = serializer.validated_data["source"]
        filtered_source = []

        for source in source[:5]:
            if source not in filtered_source:
                filtered_source.append(source)

        results = async_to_sync(search)(query, filtered_source)

        movies = Movie.objects.bulk_create(
            results,
            update_conflicts=True,
            update_fields=["title", "description", "poster", "url", "source"],
            unique_fields=["external_id"]
        )

        serializer = MovieSerializer(movies, many=True)
        return Response({"movies": serializer.data})


class MovieView(APIView):
    def get(self, request: Request, pk: int):
        movie = Movie.objects.filter(id=pk).first()

        if movie is None:
            raise Http404("Movie not found")

        new_movie, episodes = async_to_sync(fill)(movie)
        new_movie.save(update_fields=["fill_title", "fill_description", "fill_poster", "meta"])

        translations = []
        for episode in episodes:
            if episode.translation in translations:
                continue

            translations.append(episode.translation)

        Translation.objects.bulk_create(
            translations,
            update_conflicts=True,
            update_fields=["title", "meta"],
            unique_fields=["external_id"]
        )

        MovieEpisode.objects.bulk_create(
            episodes,
            update_conflicts=True,
            update_fields=["season", "episode", "meta"],
            unique_fields=["external_id"]
        )

        history, _ = History.objects.update_or_create(movie=new_movie)
        history.updated_at = timezone.now()
        history.save()

        serializer = MovieSerializer(new_movie)
        return Response(serializer.data)


class MovieEpisodeView(APIView):
    def get(self, request: Request, pk: int):
        episode = MovieEpisode.objects.filter(id=pk).first()

        if episode is None:
            raise Http404("Movie not found")

        movie = episode.movie
        translation = episode.translation

        new_episode = async_to_sync(fill_episode)(episode)
        new_episode.save(update_fields=["meta", "stream"])

        serializer = MovieEpisodeSerializer(new_episode)
        return Response(serializer.data)


class MovieEpisodeStreamView(APIView):
    def get(self, request: Request, pk: int):
        episode = MovieEpisode.objects.filter(id=pk).first()
        if episode is None:
            return Response({"error": "Movie not found"}, status=404)

        segment_url = request.query_params.get('segment_url')
        quality_url = request.query_params.get('quality_url')
        headers = episode.meta.get("stream_headers", {})

        if episode.meta.get("socket"):
            socket = Socket.objects.filter(episode_id=pk).order_by('-created_at').first()
            edge_hash = socket.data.get("edge_hash")
            if edge_hash:
                headers["accepts-controls"] = edge_hash

        if segment_url:
            url = base64.urlsafe_b64decode(segment_url.encode()).decode()
            return self._proxy_stream(request, url, headers)

        if quality_url:
            stream = base64.urlsafe_b64decode(quality_url.encode()).decode()
        else:
            stream = episode.stream

        return self._process_manifest(request, stream, headers, pk)

    def _process_manifest(self, request, stream_url, headers, pk):
        try:
            print(stream_url)
            response = requests.get(stream_url, headers=headers, timeout=10)
            playlist = m3u8.loads(response.text, uri=stream_url)

            proxy_base_url = request.build_absolute_uri(reverse('stream', args=[pk]))
            for media in playlist.media:
                if media.uri:
                    encoded = base64.urlsafe_b64encode(media.absolute_uri.encode()).decode()
                    media.uri = f"{proxy_base_url}?quality_url={encoded}"

            if playlist.playlists:
                for sub_playlist in playlist.playlists:
                    encoded = base64.urlsafe_b64encode(sub_playlist.absolute_uri.encode()).decode()
                    sub_playlist.uri = f"{proxy_base_url}?quality_url={encoded}"

            if playlist.segments:
                for segment in playlist.segments:
                    encoded = base64.urlsafe_b64encode(segment.absolute_uri.encode()).decode()
                    segment.uri = f"{proxy_base_url}?segment_url={encoded}"

            return HttpResponse(
                playlist.dumps(),
                content_type="application/vnd.apple.mpegurl"
            )
        except Exception as e:
            logger.exception(e)

            return Response({"error": str(e)}, status=500)

    def _proxy_stream(self, request, url, headers):
        proxy_headers = headers.copy()

        if 'Range' in request.headers:
            proxy_headers['Range'] = request.headers['Range']

        r = requests.get(url, headers=proxy_headers, stream=True, timeout=15)

        response = StreamingHttpResponse(
            r.iter_content(chunk_size=1024 * 64),
            status=r.status_code,
            content_type=r.headers.get('Content-Type', 'video/MP2T')
        )

        hop_by_hop_header = {
            'connection',
            'keep-alive',
            'transfer-encoding',
            'upgrade',
            'proxy-authenticate',
            'proxy-authorization',
            'te',
            'trailers',
        }

        for h, v in r.headers.items():
            if h.lower() not in hop_by_hop_header:
                response[h] = v

        return response
