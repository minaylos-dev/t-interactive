<template>
    <div class="flex-col grow items-center justify-center min-h-screen pb-48">
        <div class="flex flex-col w-full h-full justify-end items-center min-h-screen pb-28 gap-20">
            <div class="flex items-start justify-center w-2/3 gap-10">
                <h1 class="font-tinkoff text-white text-3xl font-medium">Обскура</h1>
                <p class="font-tinkoff text-white text-lg font-normal">
                    Сбылось пророчество Оскара Уайльда: машины взяли на себя всё, и человек занялся творчеством.
                    Экономика автоматизирована на 97%, и почти каждый житель планеты считает себя художником или
                    творцом. Все живут на базовый доход, но 3% занятых в реальном производстве контролируют то, от чего
                    зависят остальные
                </p>
            </div>
            <RouterLink to="/">
                <p class="font-tinkoff text-white text-2xl text-center">Результат</p>
            </RouterLink>
        </div>
    </div>

    <PlanetScene class="absolute inset-0 -z-10 -translate-x-[15%] -translate-y-[27%]" />
</template>

<script setup>
import PlanetScene from '../components/PlanetScene.vue'
</script>