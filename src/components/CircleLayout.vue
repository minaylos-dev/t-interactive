<template>
    <div ref="container" class="circle-wrap">
        <div class="circle-viewport" :style="{ width: size, height: size }">
            <slot />
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({
    // size can be CSS unit string like '90vmin' or '600px'
    size: { type: String, default: '90vmin' }
})
const container = ref(null)
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
    box-shadow: 0 0 0 2px rgba(255,255,255,0.02) inset;
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
