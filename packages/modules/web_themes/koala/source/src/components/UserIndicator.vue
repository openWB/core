<template>
  <div id="user-indicator" v-if="userManagementActive">
    <q-dialog v-model="showLogoutDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="logout" color="warning" text-color="white" />
          <span class="q-ml-sm">Willst Du Dich wirklich abmelden?</span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            flat
            label="Abmelden"
            color="negative"
            v-close-popup
            @click="logout"
          />
          <q-btn flat label="Schließen" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="showLoginDialog" persistent @hide="clearLoginData">
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="login" color="warning" text-color="white" />
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
              :rules="[
                (value) =>
                  (value && value.length > 0) || 'Benutzername erforderlich',
              ]"
            >
              <template v-slot:prepend>
                <q-icon name="account_circle" />
              </template>
            </q-input>
            <q-input
              v-model="password"
              label="Kennwort"
              type="password"
              dense
              :rules="[
                (value) =>
                  (value && value.length > 0) || 'Passwort erforderlich',
              ]"
            >
              <template v-slot:prepend>
                <q-icon name="key" />
              </template>
            </q-input>
          </q-card-section>

          <q-card-actions align="right">
            <q-btn flat label="Anmelden" color="positive" type="submit" />
            <q-btn
              flat
              label="Kennwort vergessen"
              color="warning"
              type="button"
              @click="
                showLoginDialog = false;
                showPasswordResetDialog = true;
              "
            />
            <q-btn
              v-if="anonymousAccessAllowed"
              flat
              label="Schließen"
              color="primary"
              v-close-popup
            />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog
      v-model="showPasswordResetDialog"
      persistent
      @hide="clearLoginData"
    >
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="login" color="warning" text-color="white" />
          <span class="q-ml-sm">Kennwort vergessen</span>
        </q-card-section>

        <q-form @submit="login">
          <q-card-section>
            <q-input
              v-model="user"
              label="Benutzername"
              type="text"
              dense
              autofocus
              :rules="[
                (value) =>
                  (value && value.length > 0) || 'Benutzername erforderlich',
              ]"
            >
              <template v-slot:prepend>
                <q-icon name="account_circle" />
              </template>
            </q-input>
            <q-input v-model="token" label="Token" type="password" dense>
              <template v-slot:prepend>
                <q-icon name="key" />
              </template>
            </q-input>
            <q-input
              v-model="password"
              label="Neues Kennwort"
              type="password"
              dense
            >
              <template v-slot:prepend>
                <q-icon name="key" />
              </template>
            </q-input>
            <q-input
              v-model="passwordConfirm"
              label="Neues Kennwort bestätigen"
              type="password"
              dense
              :rules="[
                (value) =>
                  value == password || 'Kennwörter stimmen nicht überein',
              ]"
            >
              <template v-slot:prepend>
                <q-icon name="key" />
              </template>
            </q-input>
          </q-card-section>

          <q-card-actions align="right">
            <q-btn
              flat
              label="Token anfordern"
              color="positive"
              type="button"
              @click="requestToken()"
            />
            <q-btn
              flat
              label="Kennwort zurücksetzen"
              color="primary"
              type="button"
              @click="resetPassword()"
            />
            <q-btn
              flat
              label="Schließen"
              color="negative"
              @click="
                showPasswordResetDialog = false;
                showLoginDialog = true;
              "
            />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-badge
      v-if="loggedIn && !smallScreen"
      rounded
      align="middle"
      color="primary"
      class="non-selectable"
    >
      <q-icon name="account_circle" size="sm" left />
      {{ username }}
    </q-badge>
    <q-icon
      v-if="loggedIn && smallScreen"
      name="account_circle"
      size="md"
      left
      color="primary"
    >
      <q-tooltip>Angemeldet als "{{ username }}"</q-tooltip>
    </q-icon>
    <q-btn
      v-if="loggedIn"
      icon="logout"
      dense
      flat
      round
      @click="showLogoutDialog = true"
    >
      <q-tooltip>Abmelden</q-tooltip>
    </q-btn>
    <q-icon v-if="!loggedIn" name="no_accounts" size="md" left>
      <q-tooltip>Nicht angemeldet</q-tooltip>
    </q-icon>
    <q-btn
      v-if="!loggedIn"
      icon="login"
      dense
      flat
      round
      @click="showLoginDialog = true"
    >
      <q-tooltip>Anmelden</q-tooltip>
    </q-btn>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useQuasar, QInput } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';

const $q = useQuasar();
const mqttStore = useMqttStore();

const showLogoutDialog = ref(false);
const showLoginDialog = ref(false);
const showPasswordResetDialog = ref(false);
const user = ref('');
const password = ref('');
const passwordConfirm = ref('');
const token = ref('');

const smallScreen = computed(() => {
  return $q.screen.lt.sm;
});

const userManagementActive = computed(() => {
  return mqttStore.userManagementActive === true;
});

const accessAllowed = computed(() => {
  return mqttStore.accessAllowed === true;
});

const anonymousAccessAllowed = computed(() => {
  return accessAllowed.value && !loggedIn.value;
});

const loggedIn = computed(() => {
  return $q.cookies.has('mqtt');
});

const username = computed(() => {
  if (loggedIn.value) {
    return $q.cookies.get('mqtt').split(':')[0];
  }
  return '';
});

const logout = () => {
  if ($q.cookies.has('mqtt')) {
    console.debug('Removing mqtt cookie');
    $q.cookies.remove('mqtt', { path: '/' });
    location.reload();
  } else {
    console.warn('No mqtt cookie found to remove');
  }
};

const login = () => {
  if (!user.value || user.value.length === 0) {
    showLoginDialog.value = false;
    return;
  }
  const mqttValue = `${user.value}:${password.value}`;
  $q.cookies.set('mqtt', mqttValue, {
    expires: '30d',
    path: '/',
    secure: true,
    sameSite: 'Lax',
  });
  showLoginDialog.value = false;
  location.reload();
};

const clearLoginData = () => {
  user.value = '';
  password.value = '';
  passwordConfirm.value = '';
  token.value = '';
};

const requestToken = () => {
  if (!user.value || user.value.length === 0) {
    console.error('Benutzername erforderlich.');
    return;
  }
  mqttStore.sendSystemCommand('createPasswordResetToken', {
    username: user.value,
  });
  $q.notify({
    type: 'info',
    message: `Falls der Benutzer "${user.value}" existiert und eine E-Mail-Adresse hinterlegt ist, wurde ein Token per E-Mail versendet.`,
    progress: true,
  });
};

const resetPassword = () => {
  if (
    !user.value ||
    user.value.length === 0 ||
    !token.value ||
    token.value.length === 0 ||
    !password.value ||
    password.value.length === 0 ||
    !passwordConfirm.value ||
    passwordConfirm.value.length === 0
  ) {
    if (password.value !== passwordConfirm.value) {
      $q.notify({
        type: 'negative',
        message: 'Kennwörter stimmen nicht überein.',
        progress: true,
      });
      return;
    }
    $q.notify({
      type: 'negative',
      message: 'Benutzername, Token und neues Kennwort erforderlich.',
      progress: true,
    });
    return;
  }
  mqttStore.sendSystemCommand('resetUserPassword', {
    username: user.value,
    token: token.value,
    newPassword: password.value,
  });
  $q.notify({
    type: 'info',
    message: `Falls der Benutzer "${user.value}" existiert und der Token korrekt ist, wurde das Kennwort zurückgesetzt.`,
    progress: true,
  });
};

watch(anonymousAccessAllowed, (newValue) => {
  if (userManagementActive.value && !newValue && !loggedIn.value) {
    showLoginDialog.value = true;
  } else {
    showLoginDialog.value = false;
  }
});

onMounted(() => {
  if (
    userManagementActive.value &&
    !anonymousAccessAllowed.value &&
    !loggedIn.value
  ) {
    showLoginDialog.value = true;
  }
});
</script>
