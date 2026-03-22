from django.urls import path
from .views import (
    SearchView, SourcesView,
    MovieView, MovieEpisodeView, MovieEpisodeStreamView,
    HistoryView,
)


urlpatterns = [
    path('movies/search/', SearchView.as_view(), name='search'),
    path('movie/<int:pk>/', MovieView.as_view(), name='movie'),
    path('episode/<int:pk>/', MovieEpisodeView.as_view(), name='episode'),
    path('episode/<int:pk>.m3u8', MovieEpisodeStreamView.as_view(), name='stream'),
    path('history/', HistoryView.as_view(), name='history'),
    path('sources/', SourcesView.as_view(), name='sources'),
]
