<script setup lang="ts">
import type { Movie, MovieEpisode } from '@/api/movies';
import type { MovieWatch } from '@/composables/watch';

import { useMoviesApi } from '@/composables/movies';
import { useWatchStore } from '@/stores/movies';

import { onMounted, ref, onBeforeUnmount, computed, watch } from 'vue';
import Hls from 'hls.js';

import Plyr from 'plyr';
import 'plyr/dist/plyr.css';

interface Props {
  movie: Movie
}
interface Episode {
  [key: number]: MovieEpisode
}
interface Seasons {
  [key: number]: Episode
}
interface Translation {
  [key: string]: Seasons
}
interface TranslationTitle {
  [key: string]: string
}

const { fillEpisode } = useMoviesApi();

const props = defineProps<Props>();
const videoRef = ref<HTMLVideoElement | null>(null);
const hlsInstance = ref<Hls | null>(null);
const plyrInstance = ref<Plyr | null>(null); 
const watchStore = useWatchStore();

const movie_watch = computed<MovieWatch>(() => {
  return watchStore.movies.find((el) => el.movie.id === props.movie.id) as MovieWatch;
})

const translations = computed(() => {
  const data: Translation = {};

  props.movie.episodes.forEach((episode) => {
    const tId = episode.translation.external_id;
    const season = episode.season;
    const epNum = episode.episode;

    data[tId] ??= {};
    data[tId][season] ??= {};
    data[tId][season][epNum] = episode;
  });

  return data;
});

const translation_title = computed<TranslationTitle>(() => {
  const data: TranslationTitle = {};
  props.movie.episodes.forEach((episode) => {
    data[episode.translation.external_id] = episode.translation.title
  });
  return data;
})

const translations_order = computed<string[]>(() => {
  const counts = Object.keys(translations.value).map((tId) => {
    let episodeCount = 0;
    Object.values(translations.value[tId]).forEach((season) => {
      episodeCount += Object.keys(season).length;
    });
    return { id: tId, count: episodeCount };
  });
  counts.sort((a, b) => b.count - a.count);
  return counts.map(item => item.id);
});

const selectedTId = ref<string>('');
const selectedSNum = ref<number>(movie_watch.value.season);
const selectedENum = ref<number>(movie_watch.value.episode);

let stallCount = 0;
let lastTime = 0;
let watchdogInterval: number | null = null;

const startWatchdog = (url: string) => {
  if (!videoRef.value) return;

  if (watchdogInterval) clearInterval(watchdogInterval);

  watchdogInterval = setInterval(() => {
    const video = videoRef.value;
    if (!video || video.paused) return;

    if (video.currentTime === lastTime) {
      stallCount++;
      if (stallCount >= 10) {
        console.log('Video stalled → restart stream');
        stallCount = 0;
        restartHls(url);
        watchdogInterval = null;
      }
    } else {
      stallCount = 0;
      lastTime = video.currentTime;
    }
  }, 1000);
};

const restartHls = (url: string) => {
  setTimeout(() => loadSource(url), 500); 
}

const destroyHls = () => {
  if (hlsInstance.value) {
    hlsInstance.value.destroy();
    hlsInstance.value = null;
  }
  if (watchdogInterval) {
    clearInterval(watchdogInterval);
    watchdogInterval = null;
  }
};

const destroyPlyr = () => {
  if (plyrInstance.value) {
    plyrInstance.value.destroy();
    plyrInstance.value = null;
  }
};

const loadSource = (url: string) => {
  if (!videoRef.value) return;

  const video = videoRef.value;

  destroyHls();

  video.pause();
  video.removeAttribute('src');
  video.load();

  if (Hls.isSupported()) {
    const hls = new Hls({ enableWorker: true, lowLatencyMode: true, maxBufferLength: 30, maxMaxBufferLength: 60, maxBufferHole: 0.5, fragLoadingTimeOut: 5000, startLevel: -1, });
    hlsInstance.value = hls;

    hls.loadSource(url);
    hls.attachMedia(video);

    hls.on(Hls.Events.ERROR, (_, data) => {
      console.warn('HLS error', data);
      if (data.fatal) {
        switch (data.type) {
          case Hls.ErrorTypes.MEDIA_ERROR:
            console.log('Media error → recover');
            hls.recoverMediaError();
            break;
          default:
            console.log('Fatal error → full restart');
            restartHls(url);
            break;
        }
      }
    });

    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      console.log(movie_watch.value.time)
      video.currentTime = movie_watch.value.time || 0;
      video.play().catch(() => {});
      startWatchdog(url);
    });
  }
};

onMounted(() => {
  if (videoRef.value) {
    plyrInstance.value = new Plyr(videoRef.value, {
      iconUrl: '/plyr.svg',
      controls: [
        'play-large', 'play', 'progress', 'current-time',
        'mute', 'volume', 'settings', 'fullscreen'
      ]
    });
    plyrInstance.value.on('timeupdate', () => { 
      if (plyrInstance.value && plyrInstance.value.currentTime > 1) { 
        movie_watch.value.time = Math.floor(plyrInstance.value.currentTime); 
      } 
    });
  }

  selectedTId.value = movie_watch.value.translation || translations_order.value[0] || '';
});

onBeforeUnmount(() => {
  destroyHls();
  destroyPlyr();
});

watch([translations_order], () => {
  if (selectedTId.value == '') selectedTId.value = translations_order.value[0] || '';
})

watch([selectedTId], ([newTId]) => {
  const seasons = translations.value[newTId];
  if (!seasons) return;
  if (!(selectedSNum.value in seasons)) selectedSNum.value = Number(Object.keys(seasons)[0]);
})

watch([selectedSNum], ([newSNum]) => {
  const episodes = translations.value[selectedTId.value]?.[newSNum];
  if (!episodes) return;
  if (!(selectedENum.value in episodes)) selectedENum.value = Number(Object.keys(episodes)[0]);
})

watch([selectedTId, selectedSNum, selectedENum], async ([newTId, newSNum, newENum]) => {
  if (!newTId || !newSNum || !newENum) return;
  const rawEpisode = translations.value[newTId]?.[newSNum]?.[newENum];
  if (!rawEpisode) return;

  const episode = await fillEpisode(rawEpisode);
  if (!episode?.stream) return;

  if (
    (movie_watch.value.season !== newSNum) ||
    (movie_watch.value.episode !== newENum)
  ){
    movie_watch.value.time = 0;
  }

  movie_watch.value.translation = newTId;
  movie_watch.value.season = newSNum;
  movie_watch.value.episode = newENum;

  loadSource(episode.stream);
});
</script>

<template>
  <div class="space-y-2">
    <div class="grid grid-cols-3 gap-2">
      <select v-model="selectedTId" class="cursor-pointer focus:outline-none">
        <option v-for="id in translations_order" :key="id" :value="id">
          {{ translation_title[id] }}
        </option>
      </select>

      <select v-model="selectedSNum" class="cursor-pointer focus:outline-none">
        <option v-for="s in Object.keys(translations[selectedTId] || {})" :key="s" :value="Number(s)">
          Season {{ s }}
        </option>
      </select>

      <select v-model="selectedENum" class="cursor-pointer focus:outline-none">
        <option v-for="ep in Object.keys(translations[selectedTId]?.[selectedSNum] || {})" :key="ep" :value="Number(ep)">
          Episode {{ ep }}
        </option>
      </select>
    </div>

    <div class="overflow-hidden rounded-xl border bg-black shadow-sm">
      <video ref="videoRef" class="w-full h-full" playsinline></video>
    </div>
  </div>
</template>

<style>
:root {
  --plyr-color-main: hsl(var(--primary, 221, 83%, 53%));
}
.plyr {
  border-radius: 0.75rem;
}
</style>