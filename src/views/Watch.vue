<script setup lang="ts">
import type { Movie } from "@/api/movies"
import type { MovieWatch } from "@/composables/watch"

import { useWatchStore } from '@/stores/movies'
import { useMoviesApi } from "@/composables/movies"
import { useRoute } from 'vue-router'
import { useWatch } from "@/composables/watch"

import Player from "@/components/Player.vue"
import SearchCard from "@/components/SearchCard.vue"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Card } from "@/components/ui/card"

import { ref, onMounted, computed } from "vue"

const { movies, sources, fillMovie, searchMovies, fetchSources } = useMoviesApi();
const { openMovie } = useWatch();
const watchStore = useWatchStore();
const route = useRoute();

let query = ref("");


const movie_watch = computed<MovieWatch>(() => {
  const movieId = Number(route.query.movie_id);
  return watchStore.movies.find((el) => el.movie.id === movieId) as MovieWatch;
})

const movie = computed<Movie>(() => {
  return movie_watch.value.movie as Movie;
})

onMounted(async () => {
  movie_watch.value.movie = await fillMovie(movie_watch.value.movie)
  
  query.value = movie.value.fill_title.split(':', 1)[0];

  movies.value = {};

  await fetchSources();
  await searchMovies(query.value, sources.value);
})

</script>

<template>
  <header class="flex h-13 items-center gap-2 shrink-0">
    <SidebarTrigger class="-ml-1" />
    <span class="text-lg font-bold truncate">{{ movie.fill_title || movie.title }}</span>
  </header>

  <div 
    class="flex flex-col gap-4 h-[calc(100vh-52px)] overflow-y-auto hide-scrollbar snap-y snap-mandatory scroll-smooth"
  >
    <section class="flex flex-col md:flex-row h-[calc(33vh-52px)] min-h-[400px] gap-2 shrink-0 snap-start">
      <div class="flex-1 flex flex-col gap-2 overflow-hidden">
        <div v-if="movie.fill_description" class="text-md font-medium text-justify overflow-y-auto pr-2 custom-scrollbar">
          {{ movie.fill_description }}
        </div>
        <div v-else class="flex flex-1 items-center justify-center bg-muted/20 rounded">
          <pre class="animate-pulse">Loading description...</pre>
        </div>
      </div>
      
      <div class="h-full shrink-0">
        <img 
          v-if="movie.fill_poster"
          :src="movie.fill_poster"
          class="w-full h-full object-cover rounded shadow-lg border"
          :alt="movie.fill_title"
        />
        <Card 
          v-else
          class="bg-muted/50 w-full h-full aspect-[2/3] rounded border-2 border-dashed flex items-center justify-center"
        >
          <span>No Poster</span>
        </Card>
      </div>
    </section>

    <section class="flex flex-col shrink-0 snap-start h-[calc(100vh-52px)]">
      <div class="flex-1 w-full h-full rounded-lg overflow-hidden flex items-center justify-center">
        <Player v-if="movie.episodes.length > 0" :movie="movie" :key="route.fullPath" class="w-full h-full"/>
        <div v-else class="text-center p-10">
          <span class="text-lg text-muted-foreground">There is no episodes or player is not supported :(</span>
        </div>
      </div>
    </section>

    <section v-if="Object.keys(movies).length > 0" class="flex flex-col h-[calc(100vh-52px)] shrink-0 snap-start">
      <h2 class="text-xl mb-4">
        Realted results for <span class="text-primary font-semibold">{{ query }}</span>
      </h2>
      
      <div class="flex-1 overflow-y-auto hide-scrollbar flex flex-col gap-6">
        <div v-for="(list, sourceName) in movies" :key="sourceName" class="flex flex-col gap-3">
          <h3 class="text-sm font-bold uppercase tracking-wider opacity-70">{{ sourceName }}</h3>
          <div class="flex gap-4 overflow-x-auto pb-4 hide-scrollbar snap-x">
            <SearchCard 
              v-for="item in list"
              :key="item.id"
              :movie="item"
              @click="openMovie(item)"
              class="snap-center shrink-0"
            />
          </div>
        </div>
      </div>
    </section>

  </div>
</template>