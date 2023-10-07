/*
 * App.vue
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

<template>
  <div id="app" class="m-0 p-0">
    <Navbar></Navbar>
    <div class="container-fluid p-0">
      <div class="row p-0 m-0">
        <div class="col-12 p-0 m-0">
          <!-- <router-view></router-view>-->
           <ColorsTheme></ColorsTheme> 
        </div> 
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// import { RouterView } from 'vue-router'
import ColorsTheme from './views/ColorsTheme.vue'
import Navbar from './components/Navbar.vue';

</script>

<style>
@import './assets/css/style.css';
@import './assets/fonts/fontawesome-free-6.0.0-web/css/fontawesome.min.css';
@import './assets/fonts/fontawesome-free-6.0.0-web/css/solid.min.css';

</style>
