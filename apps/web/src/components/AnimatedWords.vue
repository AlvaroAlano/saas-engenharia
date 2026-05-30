<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  words: string[]
  interval?: number
}>(), { interval: 2000 })

const current = ref(0)
let timer: ReturnType<typeof setInterval>

// longest word drives the invisible spacer width so the container never shifts
const longestWord = computed(() =>
  props.words.reduce((a, b) => a.length >= b.length ? a : b, '')
)

onMounted(() => {
  timer = setInterval(() => {
    current.value = (current.value + 1) % props.words.length
  }, props.interval)
})

onUnmounted(() => clearInterval(timer))
</script>

<template>
  <!--
    Container sizes itself to the longest word via the invisible spacer.
    overflow-hidden clips the entering/leaving words above and below.
    The animated words sit absolutely over the spacer.
  -->
  <span
    class="relative block overflow-hidden"
    :aria-label="words[current]"
    aria-live="polite"
  >
    <!-- Invisible spacer: reserves height + width of the longest word -->
    <span class="invisible select-none pointer-events-none" aria-hidden="true">
      {{ longestWord }}
    </span>

    <!-- Animated word — :key forces re-render → triggers enter transition -->
    <Transition name="aw">
      <span :key="current" class="absolute inset-0">
        {{ words[current] }}
      </span>
    </Transition>
  </span>
</template>

<style scoped>
/* Enter: slide up from below */
.aw-enter-active {
  transition: transform 0.55s cubic-bezier(0.34, 1.56, 0.64, 1),
              opacity  0.35s ease-out;
}
/* Leave: slide up out of frame, faster than enter */
.aw-leave-active {
  transition: transform 0.3s ease-in,
              opacity  0.25s ease-in;
  position: absolute;
  inset: 0;
}

.aw-enter-from {
  opacity: 0;
  transform: translateY(80%);
}
.aw-leave-to {
  opacity: 0;
  transform: translateY(-80%);
}

/* Respect OS reduced-motion: crossfade only, no slide */
@media (prefers-reduced-motion: reduce) {
  .aw-enter-active { transition: opacity 0.4s ease; }
  .aw-leave-active { transition: opacity 0.3s ease; }
  .aw-enter-from,
  .aw-leave-to    { transform: none; }
}
</style>
