import { useRouter } from "vue-router";
import { useWatchStore } from "@/stores/movies";
import type { Movie } from "@/api/movies";

export interface MovieWatch {
  movie: Movie
  url: string,
  title: string,
  image: string,
  season: number,
  episode: number,
  translation: string | null,
  time: number
}

export function useWatch() {
  const router = useRouter();
  const watchStore = useWatchStore();

  async function openMovie(movie: Movie) {
    let movie_watch: MovieWatch = {
      movie: movie,
      url: `/watch?movie_id=${movie.id}`,
      title: movie.title,
      image: movie.poster,
      season: 1,
      episode: 1,
      translation: null,
      time: 0
    }

    watchStore.addOrUpdateMovie(movie_watch);
    await router.push(movie_watch.url);
  }

  return { openMovie };
}
