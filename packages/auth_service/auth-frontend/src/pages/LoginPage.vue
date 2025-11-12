<template>
  <q-page class="flex flex-center bg-grey-2 q-pa-md">
    <q-card class="q-pa-lg shadow-2" style="width: 360px; max-width: 90vw">
      <q-card-section>
        <div class="text-h6 text-center q-mb-md">Anmeldung</div>

        <q-input dense outlined v-model="username" label="Benutzername" autofocus class="q-mb-sm" />
        <q-input
          dense
          outlined
          v-model="password"
          label="Passwort"
          type="password"
          class="q-mb-md"
          @keyup.enter="login"
        />

        <q-btn
          label="Einloggen"
          color="primary"
          class="full-width"
          :loading="loading"
          @click="login"
        />

        <q-banner v-if="error" dense class="bg-red-2 text-red-10 q-mt-md">
          Benutzername oder Passwort falsch.
        </q-banner>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';

const router = useRouter();
const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref(false);

async function login() {
  loading.value = true;
  error.value = false;
  try {
    const formData = new FormData();
    formData.append('username', username.value);
    formData.append('password', password.value);
    const res = await api.post('/login', formData);
    if (res.data.status === 'ok') {
      await router.push('/');
    } else {
      error.value = true;
    }
  } catch {
    error.value = true;
  } finally {
    loading.value = false;
  }
}
</script>
