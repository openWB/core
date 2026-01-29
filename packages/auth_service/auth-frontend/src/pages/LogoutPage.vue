<template>
  <q-page class="flex flex-center">
    <q-card class="q-pa-md text-center">
      <q-card-section>
        <div class="text-h6">Abmeldung erfolgreich</div>
      </q-card-section>
      <q-card-actions align="center">
        <q-btn
          color="primary"
          label="Zur Anmeldung"
          icon-right="login"
          @click="goLogin"
        />
        <q-btn
          color="primary"
          label="Zur Startseite"
          icon-right="home"
          @click="goHome"
        />
      </q-card-actions>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
const router = useRouter();

async function goLogin() {
  document.cookie = 'mqtt_auth=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT';
  await router.push('/login');
}

async function goHome() {
  document.cookie = 'mqtt_auth=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT';
  await router.push('/');
}
</script>
