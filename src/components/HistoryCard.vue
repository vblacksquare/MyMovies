<script setup lang="ts">
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { History } from '@/api/movies'

interface Props {
  history: History
}

defineEmits(['click']);
const props = defineProps<Props>();

</script>

<template>
  <Card
    @click="$emit('click')"
    class="flex-none h-[35vw] w-[25vw] relative overflow-hidden group cursor-pointer"
  >
    
    <img 
      :src="props.history.movie.fill_poster" 
      :alt="props.history.movie.fill_title"
      class="absolute inset-0 w-full h-full object-cover object-[50%_80%] transition-all duration-500 group-hover:scale-120"
    />

    <div class="absolute top-4 right-4 z-10">
      <span class="bg-black/20 backdrop-blur-md text-white text-xs font-small px-3 py-1 rounded">
        {{ 
          new Date(props.history.updated_at).toLocaleString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          }).replace(',', '') 
        }}
      </span>
    </div>

    <div class="absolute bottom-0 w-full bg-black/40 backdrop-blur-md border-t border-white/10 text-white">
      <CardHeader class="p-4">
        <CardTitle class="text-md font-bold">
          {{ props.history.movie.fill_title }}
        </CardTitle>
      </CardHeader>

      <CardContent class="p-4 pt-0">
        <p class="text-sm text-gray-200 line-clamp-2">
          {{ props.history.movie.fill_description }}
        </p>
      </CardContent>

      <CardFooter class="p-4 pt-0">
        <Button variant="outline" size="sm" class="cursor-pointer w-full bg-white/10 hover:bg-white/20 hover:text-white border-white/20 text-white">
          Continue
        </Button>
      </CardFooter>
    </div>
  </Card>
</template>