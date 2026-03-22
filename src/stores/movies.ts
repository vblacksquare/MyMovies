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

      const index = this.movies.findIndex(el => el.movie.id === movieId);

      if (index !== -1) {
        const existing = this.movies.splice(index, 1)[0];
        this.movies.unshift(existing);
      } else {
        this.movies.unshift(movie_watch);
      }

      this.movies = Array.from(new Map(this.movies.map(el => [el.movie.id, el])).values());

      if (this.movies.length > 5) {
        this.movies = this.movies.slice(0, 5);
      }

      return this.movies;
    }
  },
  persist: true
});