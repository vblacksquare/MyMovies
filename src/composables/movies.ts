import { ref } from 'vue';
import type { Movie, MovieEpisode, MoviesResponse, SourcesResponse, HistoryResponse, History } from '@/api/movies';
import { fill, getSources, search, getHistory, fillMovieEpisode } from '@/api/movies';


export interface Movies {
  [key: string]: Movie[]
}


export function useMoviesApi() {
  const movies = ref<Movies>({});
  const history = ref<History[]>([]);
  const sources = ref<string[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fillMovie(movie: Movie) {
    loading.value = true;
    error.value = null;
    try {
      movie = await fill(movie);
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }

    return movie;
  }

  async function fillEpisode(episode: MovieEpisode) {
    loading.value = true;
    error.value = null;
    try {
      episode = await fillMovieEpisode(episode);
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }

    return episode;
  }

  async function fetchSources() {
    loading.value = true;
    error.value = null;
    try {
      const data: SourcesResponse = await getSources();
      sources.value = data.sources;
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }

  async function fetchHistory() {
    loading.value = true;
    error.value = null;
    
    try {
      const data: HistoryResponse = await getHistory();
      history.value = data.history;
      
    } catch (e: any) {
      if (e.name === 'AbortError') return;
      error.value = e.message;
      history.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function searchMovies(query: string, selectedSources: string[], signal?: AbortSignal) {
    loading.value = true;
    error.value = null;
    
    try {
      if (!query.trim()){
        movies.value = {};

      } else {
        const data: MoviesResponse = await search(query, selectedSources, signal);

        const groupedMovies: Movies = {};

        data.movies.forEach((el) => {
          if (!groupedMovies[el.source]) {
            groupedMovies[el.source] = [];
          }
          groupedMovies[el.source].push(el);
        });

        movies.value = groupedMovies;
      }
      
    } catch (e: any) {
      if (e.name === 'AbortError') return;
      error.value = e.message;
      movies.value = {};
    } finally {
      loading.value = false;
    }
  }

  return { movies, history, sources, loading, error, fetchSources, searchMovies, fillMovie, fillEpisode, fetchHistory };
}
