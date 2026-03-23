<script setup lang="ts">
import type { SidebarProps } from "@/components/ui/sidebar"

import { GalleryVerticalEnd, HomeIcon, FilmIcon, ChevronRight, TrashIcon } from "lucide-vue-next"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"
import {
  ContextMenu,
  ContextMenuTrigger,
  ContextMenuContent,
  ContextMenuItem
} from "@/components/ui/context-menu"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

import { useWatchStore } from '@/stores/movies';
import { useWatch } from '@/composables/watch'
import { useRoute } from 'vue-router'

import { ref, computed } from "vue"

const props = withDefaults(defineProps<SidebarProps>(), {
  variant: "floating",
})

const watchStore = useWatchStore();
const { openMovie } = useWatch();
const route = useRoute();

const data = ref([
  {
    title: "Home",
    url: "/",
    icon: HomeIcon,
  },
])

const watch_data = computed(() => ({
  title: "Watch",
  url: "/",
  icon: FilmIcon,
  items: watchStore.movies 
}))

const formatTime = (totalSeconds: number | undefined): string => {
  if (!totalSeconds || isNaN(totalSeconds)) return '00:00';

  const hrs = Math.floor(totalSeconds / 3600);
  const mins = Math.floor((totalSeconds % 3600) / 60);
  const secs = Math.floor(totalSeconds % 60);

  const m = mins.toString().padStart(2, '0');
  const s = secs.toString().padStart(2, '0');

  if (hrs > 0) {
    return `${hrs}:${m}:${s}`;
  }

  return `${m}:${s}`;
};

</script>

<template>
  <Sidebar v-bind="props">
    <SidebarHeader>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton size="lg" as-child>
            <RouterLink :to="'/'">
              <div class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <GalleryVerticalEnd class="size-4" />
              </div>
              <div class="flex flex-col gap-0.5 leading-none">
                <span class="font-medium">My Movies</span>
              </div>
            </RouterLink>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarHeader>
    <SidebarContent>
      <SidebarGroup>
        <SidebarMenu class="gap-2">
          <SidebarMenuItem v-for="item in data" :key="item.title">
            <RouterLink :to="item.url">
              <SidebarMenuButton 
                class="cursor-pointer"
                :is-active="item.title == route.meta.title">
                <component :is="item.icon" />
                <span class="font-medium">{{ item.title }}</span>
              </SidebarMenuButton>
            </RouterLink>
          </SidebarMenuItem>

          <Collapsible
            v-if="(watch_data.items.length > 0)"
            as-child
            :default-open="true"
            class="group/collapsible"
          >
            <SidebarMenuItem>
              <CollapsibleTrigger as-child>
                <SidebarMenuButton :tooltip="watch_data.title" class="cursor-pointer">
                  <component :is="watch_data.icon" v-if="watch_data.icon" />
                  <span>{{ watch_data.title }}</span>
                  <ChevronRight class="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                </SidebarMenuButton>
              </CollapsibleTrigger>
              <CollapsibleContent class="pr-1">
                <SidebarMenuSub class="w-full max-h-[70vh] overflow-y-auto hide-scrollbar">
                  <SidebarMenuSubItem
                    v-for="subItem in watch_data.items"
                    :key="subItem.title"
                  >
                    <ContextMenu>
                      
                      <ContextMenuTrigger as-child>
                        <SidebarMenuSubButton 
                          class="cursor-pointer w-full h-auto py-2 px-2 flex items-center min-w-0"
                          @click="openMovie(subItem.movie)"
                          :is-active="subItem.url == route.fullPath"
                        >
                          <div class="flex gap-2 w-full min-w-0 items-start h-full">
                            <img 
                              v-if="subItem.image" 
                              :src="subItem.image" 
                              class="w-10 h-14 shrink-0 rounded object-cover"
                            />
                            
                            <div class="flex flex-col h-14 justify-between flex-1 min-w-0">
                              <p class="text-[11px] leading-tight font-medium line-clamp-2 break-words text-left">
                                {{ subItem.title }}
                              </p>
                              
                              <p class="text-[10px] text-muted-foreground opacity-70">
                                s: {{ subItem.season }} e: {{ subItem.episode }} {{ formatTime(subItem.time) }}
                              </p>
                            </div>
                          </div>
                        </SidebarMenuSubButton>
                      </ContextMenuTrigger>

                      <ContextMenuContent>
                        <ContextMenuItem @click="watchStore.removeMovie(subItem.movie.id)">
                          <TrashIcon />
                          Remove
                        </ContextMenuItem>
                      </ContextMenuContent>

                    </ContextMenu>
                  </SidebarMenuSubItem>
                </SidebarMenuSub>
              </CollapsibleContent>
            </SidebarMenuItem>
          </Collapsible>
        </SidebarMenu>
      </SidebarGroup>
    </SidebarContent>
  </Sidebar>
</template>
