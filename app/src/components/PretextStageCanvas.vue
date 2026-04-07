<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { renderPretextStage, type PretextStage } from '../stage/renderPretextStage'

const props = defineProps<{
  stage: PretextStage
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)

let frameId = 0
let observer: ResizeObserver | null = null

function draw(): void {
  if (canvasRef.value) {
    renderPretextStage(canvasRef.value, props.stage, performance.now())
  }

  frameId = window.requestAnimationFrame(draw)
}

onMounted(() => {
  if (canvasRef.value) {
    observer = new ResizeObserver(() => {
      if (canvasRef.value) {
        renderPretextStage(canvasRef.value, props.stage, performance.now())
      }
    })
    observer.observe(canvasRef.value)
  }

  frameId = window.requestAnimationFrame(draw)
})

watch(
  () => props.stage,
  () => {
    if (canvasRef.value) {
      renderPretextStage(canvasRef.value, props.stage, performance.now())
    }
  },
  { deep: true },
)

onBeforeUnmount(() => {
  if (frameId) {
    window.cancelAnimationFrame(frameId)
  }

  observer?.disconnect()
})
</script>

<template>
  <div class="stage-canvas-shell">
    <canvas ref="canvasRef" class="stage-canvas" />
  </div>
</template>

<style scoped>
.stage-canvas-shell {
  position: relative;
  min-height: 100%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(130deg, rgba(255, 255, 255, 0.05) 0 10%, transparent 10% 100%),
    radial-gradient(circle at 74% 28%, rgba(29, 182, 255, 0.18), transparent 26%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), transparent 42%),
    #050810;
  overflow: hidden;
  clip-path: polygon(0 0, 100% 0, 100% 94%, 95% 100%, 0 100%);
}

.stage-canvas-shell::before {
  content: "";
  position: absolute;
  inset: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  pointer-events: none;
}

.stage-canvas {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 620px;
}

@media (max-width: 720px) {
  .stage-canvas {
    min-height: 380px;
  }
}
</style>
