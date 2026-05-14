.template-block {
}

<template>
    <div ref="container" class="circle-wrap" :style="wrapStyle">
        <div class="circle-viewport" :style="{ width: size, height: size }">
            <slot />
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import transformConfig from '../config/uniform-transform.json'

const props = defineProps({
    // size can be CSS unit string like '90vmin' or '600px'
    size: { type: String, default: '508px' }
})
const container = ref(null)

const scaleVal = Number(transformConfig.scale ?? 1)
const offsetX = Number(transformConfig.offset?.x ?? 0)
const offsetY = Number(transformConfig.offset?.y ?? 0)

const wrapStyle = computed(() => ({
    transform: `translate(${offsetX}px, ${offsetY}px) scale(${scaleVal})`,
    transformOrigin: 'center center'
}))
</script>

<style scoped>
.circle-wrap {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #000; /* dark outside area */
    pointer-events: none; /* allow clicks only inside viewport */
}
.circle-viewport {
    border-radius: 50%;
    overflow: hidden;
    box-shadow: 0 0 0 2px rgba(255,255,255,0.1) inset;
    background: transparent;
    pointer-events: auto; /* enable interactions inside the circle */
    display: block;
}

/* Make sure the inner content fills the circular viewport */
.circle-viewport {
    width: 100%;
    height: 100%;
    display: block;
    position: relative;
}
</style>
