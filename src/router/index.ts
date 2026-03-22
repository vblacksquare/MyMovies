import { createRouter, createWebHashHistory } from 'vue-router'
import { useWatchStore } from '@/stores/movies'

import PageView from '@/views/Page.vue'
import HomeView from '@/views/Home.vue'
import WatchView from '@/views/Watch.vue'


const routes = [
  {
    path: '/',
    component: PageView,
    children: [
      {
        path: '',
        component: HomeView,
        meta: { title: 'Home' }
      },
      {
        path: 'watch',
        component: WatchView,
        meta: { title: 'Watch' }
      }
    ]
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to, _, next) => {
  if (to.path === '/watch') {
    const movieId = to.query.movie_id;

    if (!movieId) {
      return next('/');
    }

    const watchStore = useWatchStore();
    const movie_watch = watchStore.movies.find((el) => el.movie.id === Number(movieId))

    if (!movie_watch){
      return next('/');
    }
  }

  next();
});

export default router
