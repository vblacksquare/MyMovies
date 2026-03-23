<script setup lang="ts">
import { InputGroup, InputGroupAddon, InputGroupInput } from "@/components/ui/input-group"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { SearchIcon } from "lucide-vue-next"
import { ref, onMounted } from 'vue';
import { useMoviesApi } from '@/composables/movies';
import { useWatch } from '@/composables/watch'
import { useSearchStore } from '@/stores/movies';
import { watchDebounced } from "@vueuse/core";
import { Card } from "@/components/ui/card"
import HistoryCard from "@/components/HistoryCard.vue";


const { movies, history, sources, fetchHistory, fetchSources, searchMovies } = useMoviesApi();
const { openMovie } = useWatch();

const searchStore = useSearchStore();

const isFocused = ref(false);

onMounted(async () => {
  await fetchSources();
  await searchMovies(searchStore.query, sources.value);
  await fetchHistory();
});

watchDebounced(
  () => searchStore.query,
  async (value, _, onCleanup) => {
    const controller = new AbortController();
    onCleanup(() => controller.abort());

    await searchMovies(value, sources.value, controller.signal);
  },
  { debounce: 300 }
);

</script>

<template>
  <header class="flex h-13 shrink-0 items-center gap-2 bg-background">
    <SidebarTrigger class="-ml-1" />
    
    <InputGroup>
      <InputGroupInput 
        v-model="searchStore.query" 
        @focus="isFocused = true"
        @blur="isFocused = false"
        placeholder="Search..." 
      />
      <InputGroupAddon align="inline-start">
        <SearchIcon class="text-muted-foreground w-4 h-4" />
      </InputGroupAddon>
    </InputGroup>

    <div 
      v-if="isFocused && searchStore.query" 
      class="absolute top-14 right-2 w-[calc(100vw-270px)] bg-primary-foreground border rounded shadow-2xl z-50 max-h-[70vh] overflow-y-auto hide-scrollbar"
    >
    
      <div class="p-2 space-y-1">
        <div v-for="(list, sourceName) in movies" :key="sourceName" class="source-section">
  
          <h3 class="text-lg font-bold">{{ sourceName }}</h3>
          
          <div 
            v-for="movie in list" 
            :key="movie.id"
            class="flex items-center gap-4 p-3 hover:bg-muted rounded-lg cursor-pointer transition-colors"
            @mousedown.prevent="openMovie(movie)"
          >
            <img 
              v-if="movie.poster" 
              :src="movie.poster" 
              class="w-12 h-16 object-cover rounded"
            />
            <span>{{ movie.title }}</span>
          </div>
        </div>
        
        <div v-if="Object.keys(movies).length === 0" class="p-4 text-center text-sm text-muted-foreground">
          Nothing found :x
        </div>
      </div>
    </div>
  </header>

  <div class="flex flex-col gap-4 h-[calc(100vh-64px)] overflow-y-auto hide-scrollbar">
    <div class="w-full flex flex-col gap-2">
      <span>Last watched</span>
      <div v-if="history.length > 0" class="pb-2 w-full flex gap-2 overflow-x-auto hide-scrollbar">
        <HistoryCard
          v-for="item in history" 
          :key="item.movie.id"
          :history="item"
          @click="openMovie(item.movie)"
        />
      </div>
      <div v-if="history.length == 0" class="pb-2 w-full flex gap-2 overflow-x-auto hide-scrollbar">
        <Card 
          v-for="i in [1, 2, 3, 4, 5]"
          :key="i"
          class="bg-muted/50 flex-none h-[35vw] w-[25vw] relative overflow-hidden group cursor-pointer"
        />
      </div>
    </div>
  </div>
</template>