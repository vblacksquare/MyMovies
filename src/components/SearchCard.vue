<script setup lang="ts">
import { Button } from "@/components/ui/button"
import {
  Card,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { Movie } from '@/api/movies'

interface Props {
  movie: Movie
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
      :src="movie.poster" 
      :alt="movie.title"
      class="absolute inset-0 w-full h-full object-cover object-[50%_80%] transition-all duration-500 group-hover:scale-120"
    />

    <div class="absolute bottom-0 w-full bg-black/40 backdrop-blur-md border-t border-white/10 text-white">
      <CardHeader class="p-4">
        <CardTitle class="text-md font-bold">
          {{ movie.title }}
        </CardTitle>
      </CardHeader>

      <CardFooter class="p-4 pt-0">
        <Button variant="outline" size="sm" class="cursor-pointer w-full bg-white/10 hover:bg-white/20 hover:text-white border-white/20 text-white">
          Continue
        </Button>
      </CardFooter>
    </div>
  </Card>
</template>