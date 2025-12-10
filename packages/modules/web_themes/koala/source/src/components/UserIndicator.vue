<template>
  <div id="user-indicator" v-if="userManagementActive">
    <q-dialog v-model="showLogoutDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="logout" color="warning" text-color="white" />
          <span class="q-ml-sm">Willst Du Dich wirklich abmelden?</span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Abmelden" color="negative" v-close-popup @click="logout" />
          <q-btn flat label="Schließen" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="showLoginDialog" persistent @hide="clearLoginData">
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="logout" color="warning" text-color="white" />
          <span class="q-ml-sm">Gib Deine Anmeldedaten ein.</span>
        </q-card-section>

        <q-form @submit="login">
          <q-card-section>
            <q-input
              v-model="user"
              label="Benutzername"
              type="text"
              dense
              autofocus
              :rules="[ value => value && value.length > 0 || 'Benutzername erforderlich']"
            >
              <template v-slot:prepend>
                <q-icon name="account_circle" />
              </template>
            </q-input>
            <q-input
              v-model="password"
              label="Passwort"
              type="password"
              dense
              :rules="[ value => value && value.length > 0 || 'Passwort erforderlich']"
            >
              <template v-slot:prepend>
                <q-icon name="key" />
              </template>
            </q-input>
          </q-card-section>

          <q-card-actions align="right">
            <q-btn flat label="Anmelden" color="positive" type="submit" />
            <q-btn flat label="Schließen" color="primary" v-close-popup />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-badge v-if="loggedIn && !smallScreen" rounded align="middle" color="primary" class="non-selectable">
      <q-icon name="account_circle" size="sm" left />
      {{ username }}
    </q-badge>
    <q-icon v-if="loggedIn && smallScreen" name="account_circle" size="md" left color="positive">
      <q-tooltip>Angemeldet als "{{ username }}"</q-tooltip>
    </q-icon>
    <q-btn v-if="loggedIn" icon="logout" dense flat round @click="showLogoutDialog = true">
      <q-tooltip>Abmelden</q-tooltip>
    </q-btn>
    <q-btn v-else icon="login" dense flat round @click="showLoginDialog = true">
      <q-tooltip>Anmelden</q-tooltip>
    </q-btn>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useQuasar, QInput } from 'quasar';
import { useRouter } from 'vue-router';
import { useMqttStore } from 'src/stores/mqtt-store';

const $q = useQuasar();
const router = useRouter();
const mqttStore = useMqttStore();

const showLogoutDialog = ref(false);
const showLoginDialog = ref(false);
const user = ref('');
const password = ref('');

const smallScreen = computed(() => {
  return $q.screen.lt.sm;
});

const userManagementActive = computed(() => {
  return mqttStore.userManagementActive === true;
});

const loggedIn = computed(() => {
  return $q.cookies.has('mqtt');
});

const username = computed(() => {
  if (loggedIn.value){
    return $q.cookies.get('mqtt').split(':')[0];
  }
  return '';
});

const logout = () => {
  console.log('cookies:', $q.cookies.getAll());
  if ($q.cookies.has('mqtt')) {
    console.log('Removing mqtt cookie');
    $q.cookies.remove('mqtt', { path: '/' });
    router.go(0);
  } else {
    console.log('No mqtt cookie found to remove');
  }
};

const login = () => {
  console.log('Logging in with user:', user.value);
  if (!user.value || user.value.length === 0) {
    showLoginDialog.value = false;
    return;
  }
  const mqttValue = `${user.value}:${password.value}`;
  $q.cookies.set('mqtt', mqttValue, { expires: '30d', path: '/', secure: true, sameSite: 'Lax' });
  showLoginDialog.value = false;
  router.go(0);
};

const clearLoginData = () => {
  user.value = '';
  password.value = '';
};
</script>
