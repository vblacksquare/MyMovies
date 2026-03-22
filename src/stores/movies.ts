import { defineStore } from 'pinia';
import type { MovieWatch } from '@/composables/watch'

export const useSearchStore = defineStore('search', {
  state: () => ({
    query: ''
  }),
  persist: true
});

export const useWatchStore = defineStore('watch', {
  state: () => ({
    movies: [] as MovieWatch[]
  }),
  actions: {
    addOrUpdateMovie(movie_watch: MovieWatch) {
      const movieId = movie_watch.movie.id;

      let old_movie_watch = this.movies.find((el) => el.movie.id == movieId)
      if (old_movie_watch){
        movie_watch = old_movie_watch;
      }

      const filtered = this.movies.filter(
        (el) => el.movie.id !== movieId
      );
      const updated = [movie_watch, ...filtered];

      this.movies = updated.slice(0, 5);
      return this.movies;
    }
  },
  persist: true
});