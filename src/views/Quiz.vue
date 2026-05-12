<script setup lang="ts">
import { R } from 'vue-router/dist/index-D_VEAp3P.js';

</script>

<template>
    <div class="flex flex-col items-center justify-center grow h-full py-20">
        <h1 class="font-tinkoff text-white text-6xl text-center mb-10">Деятельность</h1>
        <ul class="flex flex-col gap-3">
            <li class="font-tinkoff text-white text-2xl">Бизнес</li>
            <li class="font-tinkoff text-white text-2xl">Технологии</li>
            <li class="font-tinkoff text-white text-2xl">Наука</li>
            <li class="font-tinkoff text-white text-2xl">Искусство <br/>и творчество</li>
        </ul>       
    </div>
    <div class="absolute bottom-20 left-1/2 -translate-x-1/2">
        <RouterLink to="/result">
             <p class="font-tinkoff text-white text-2xl text-center">Выбери параметр</p>
        </RouterLink>
    </div>
</template> 