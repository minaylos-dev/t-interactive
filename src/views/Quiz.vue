<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import questions from '../assets/questions.json'
import { useQuizStore } from '../stores/quiz'

const store = useQuizStore()
const router = useRouter()
const index = ref(0)
const total = questions.length

const current = computed(() => questions[index.value])
const selected = (q) => store.getAnswer(q.id)

function selectVariant(variantId) {
    store.setAnswer(current.value.id, variantId)
}

function next() {
    if (index.value < total - 1) index.value++
    else router.push('/result')
}

function prev() {
    if (index.value > 0) index.value--
}
</script>

<template>
    <div class="flex flex-col items-center justify-center grow h-full py-12 px-6">
        <div class="w-full max-w-2xl">
            <h2 class="text-white text-3xl mb-6">{{ current.text }}</h2>

            <ul class="grid gap-3">
                <li v-for="variant in current.variants" :key="variant.id">
                    <button @click="selectVariant(variant.id)" :class="{
                        'w-full text-left p-4 rounded': true,
                        'border': selected(current) === variant.id,
                    }">
                        <span class="text-white text-lg">{{ variant.text }}</span>
                    </button>
                </li>
            </ul>

            <div class="mt-6 flex justify-between">
                <button @click="prev" class="px-4 py-2 text-white">Back</button>
                <div class="flex gap-3">
                    <button @click="next" class="px-4 py-2 text-white">Next</button>
                </div>
            </div>
        </div>
    </div>
</template>
