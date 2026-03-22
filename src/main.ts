import { createApp } from 'vue';
import { createPinia } from 'pinia';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue';
import router from './router';
import './style.css';


const app = createApp(App);
const pinia = createPinia();
pinia.use(piniaPluginPersistedstate)

console.log(app)

app.use(pinia);
app.use(router);
app.mount('#app');
