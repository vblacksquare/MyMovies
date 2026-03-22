<script lang="ts">
export const iframeHeight = "800px"
export const description = "A floating sidebar with submenus."
</script>

<script setup lang="ts">
import AppSidebar from "@/components/AppSidebar.vue"
import {
  SidebarInset,
  SidebarProvider
} from "@/components/ui/sidebar"

</script>

<template>
  <SidebarProvider :style="{ '--sidebar-width': '14rem' }">
    <AppSidebar />
    <SidebarInset class="px-2 w-1">
      <router-view />
    </SidebarInset>
  </SidebarProvider>
</template>
