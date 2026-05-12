<template>
    <div class="hidden flex-col grow items-end justify-end min-h-screen pb-48">
        <div class="flex w-full justify-center">
            <div class="flex items-start justify-center w-2/3 gap-10">
                <h1 class="font-tinkoff text-white text-3xl">Название<br /> планеты</h1>
                <p class="font-tinkoff text-white text-lg">
                    Lorem ipsum dolor sit amet consectetur
                    adipisicing elit. Eaque quidem cupiditate nihil, aperiam quaerat quibusdam! Qui assumenda temporibus
                    magni modi veritatis Lorem ipsum dolor, sit amet consectetur adipisicing elit. Blanditiis quibusdam
                    esse porro vitae veniam voluptates vel ipsum iusto, at ex modi voluptas labore sapiente quisquam
                    illo eos fuga quod. Nemo!
                </p>
            </div>
        </div>
    </div>

    <PlanetScene class="absolute inset-0 -z-10" />

    <div class="absolute bottom-20 left-1/2 -translate-x-1/2">
        <RouterLink to="/">
            <p class="font-tinkoff text-white text-2xl text-center">Результат</p>
        </RouterLink>
    </div>
</template>

<script setup>
import PlanetScene from '../components/PlanetScene.vue'
</script>