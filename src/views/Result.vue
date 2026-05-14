<template>
    <div class="flex-col grow items-center justify-end min-h-full">
        <div
            class="flex flex-col w-full max-h-[190px] h-full justify-between items-center absolute bottom-4 left-1/2 -translate-x-1/2">
            <div class="flex items-start justify-center pl-[50px] pr-9 gap-5">
                <h1 class="font-tinkoff text-white text-[38px] leading-[93%] -tracking-[0.04em] font-medium">Название
                    <br /> Планеты</h1>
                <p class="font-tinkoff text-white text-base leading-[93%] font-normal">
                    Разнообразный и богатый опыт начало повседневной работы по формированию позиции требуют определения
                    и уточнения систем массового участия. Значимость этих проблем настолько очевидна.
                </p>
            </div>
            <RouterLink class="" to="/">
                <p class="font-tinkoff font-normal text-white text-xl -tracking-[0.04em] leading-[93%] text-center">Результат</p>
            </RouterLink>
        </div>
    </div>

    <PlanetScene class="absolute inset-0 -z-10 -translate-x-[12%] -translate-y-[33%]" />
</template>

<script setup>
import PlanetScene from '../components/PlanetScene.vue'
</script>