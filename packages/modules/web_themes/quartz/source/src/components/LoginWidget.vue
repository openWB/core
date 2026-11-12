<template>
  <!-- Both banners are independent of connected/userManagementActive on purpose: client.end()
       in the store's CONNACK-rejection handler flips connected to false in the same tick, so
       gating authFailureMessage behind `connected` would hide the message explaining the drop;
       the default-creds nag likewise must survive even when user management isn't active yet -
       exactly the state a fresh admin/openwb install is in. -->
  <div
    v-if="mqttStore.defaultCredentialsWarning && !dismissedDefaultWarning"
    class="status-box status-box-warning fixed inset-x-2 top-2 z-[70] sm:inset-x-auto sm:right-2 sm:w-[360px]"
  >
    <div class="flex items-start justify-between gap-2">
      <p class="m-0">
        Es werden die Standardzugangsdaten verwendet! Bitte ändere diese aus Sicherheitsgründen.
      </p>
      <BaseIconButton
        aria-label="Schließen"
        size="sm"
        @click="dismissedDefaultWarning = true"
      >
        <IconClose />
      </BaseIconButton>
    </div>
  </div>

  <div
    v-if="mqttStore.authFailureMessage"
    class="status-box status-box-fault fixed inset-x-2 top-2 z-[70] sm:inset-x-auto sm:right-2 sm:w-[360px]"
  >
    <p class="m-0">
      {{ mqttStore.authFailureMessage }}
    </p>
    <BaseButton
      class="mt-2"
      variant="primary"
      @click="reloadPage"
    >
      Seite neu laden
    </BaseButton>
  </div>

  <div v-if="mqttStore.connected && userManagementActive">
    <!-- nav trigger -->
    <BaseIconButton
      :active="mqttStore.loggedIn"
      aria-label="Benutzerkonto"
      :title="mqttStore.loggedIn ? `Angemeldet als „${mqttStore.username}“` : 'Anmelden'"
      @click="mqttStore.loggedIn ? (showLogoutDialog = true) : (showLoginDialog = true)"
    >
      <IconUser v-if="mqttStore.loggedIn" />
      <IconLock v-else />
    </BaseIconButton>

    <!-- login dialog -->
    <BaseModal
      :model-value="showLoginDialog"
      title="Anmelden"
      @update:model-value="(v) => { if (v || anonymousAccessAllowed) showLoginDialog = v }"
    >
      <FormField
        id="login-username"
        v-model="loginUsername"
        label="Benutzername"
        autocomplete="username"
        first
      />
      <FormField
        id="login-password"
        v-model="loginPassword"
        label="Kennwort"
        type="password"
        autocomplete="current-password"
        @keyup.enter="canSubmitLogin && handleLogin()"
      />

      <div class="mt-4 flex flex-wrap items-center justify-end gap-2">
        <BaseButton
          v-if="dataProtectionAcknowledged"
          variant="secondary"
          @click="showLoginDialog = false; showResetDialog = true"
        >
          Kennwort vergessen
        </BaseButton>
        <BaseButton
          v-if="anonymousAccessAllowed"
          variant="secondary"
          @click="showLoginDialog = false"
        >
          Schließen
        </BaseButton>
        <BaseButton
          variant="primary"
          :disabled="!canSubmitLogin"
          @click="handleLogin"
        >
          Anmelden
        </BaseButton>
      </div>
    </BaseModal>

    <!-- logout confirm dialog -->
    <BaseModal
      :model-value="showLogoutDialog"
      title="Abmelden"
      @update:model-value="showLogoutDialog = $event"
    >
      <p>Willst Du Dich wirklich abmelden?</p>
      <div class="mt-4 flex items-center justify-end gap-2">
        <BaseButton
          variant="secondary"
          @click="showLogoutDialog = false"
        >
          Abbrechen
        </BaseButton>
        <BaseButton
          variant="danger"
          @click="mqttStore.logout()"
        >
          Abmelden
        </BaseButton>
      </div>
    </BaseModal>

    <!-- password reset dialog -->
    <BaseModal
      v-if="dataProtectionAcknowledged"
      :model-value="showResetDialog"
      title="Kennwort vergessen"
      @update:model-value="showResetDialog = $event"
    >
      <FormField
        id="reset-username"
        v-model="resetUsername"
        label="Benutzername"
        autocomplete="username"
        first
      />
      <FormField
        id="reset-token"
        v-model="resetToken"
        label="Token"
        type="password"
        :disabled="resetUsername.length === 0"
      />
      <FormField
        id="reset-new-password"
        v-model="resetNewPassword"
        label="Neues Kennwort"
        type="password"
        :disabled="resetUsername.length === 0 || resetToken.length === 0"
      />
      <FormField
        id="reset-confirm-password"
        v-model="resetConfirmPassword"
        label="Neues Kennwort bestätigen"
        type="password"
        :disabled="resetUsername.length === 0 || resetToken.length === 0"
      />
      <p
        v-if="resetConfirmPassword.length > 0 && resetNewPassword !== resetConfirmPassword"
        class="mode-note text-error"
      >
        Kennwörter stimmen nicht überein.
      </p>

      <div
        v-if="resetStatusMessage"
        class="status-box status-box-info mt-3"
      >
        <p class="m-0">
          {{ resetStatusMessage }}
        </p>
      </div>

      <div class="mt-4 flex flex-wrap items-center justify-end gap-2">
        <BaseButton
          variant="secondary"
          @click="showResetDialog = false; showLoginDialog = true"
        >
          Zurück
        </BaseButton>
        <BaseButton
          variant="secondary"
          :disabled="resetUsername.length === 0 || tokenRequested"
          @click="requestToken"
        >
          Token anfordern
        </BaseButton>
        <BaseButton
          variant="primary"
          :disabled="!canSubmitReset"
          @click="submitReset"
        >
          Kennwort zurücksetzen
        </BaseButton>
      </div>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, watchEffect } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import BaseModal from './BaseModal.vue'
import BaseButton from './BaseButton.vue'
import BaseIconButton from './BaseIconButton.vue'
import FormField from './FormField.vue'
import IconUser from './icons/IconUser.vue'
import IconLock from './icons/IconLock.vue'
import IconClose from './icons/IconClose.vue'

const mqttStore = useMqttStore()

const userManagementActive = computed(() => mqttStore.userManagementActive())
const dataProtectionAcknowledged = computed(() => mqttStore.dataProtectionAcknowledged())
const accessAllowed = computed(() => mqttStore.accessAllowed())
const anonymousAccessAllowed = computed(() => accessAllowed.value && !mqttStore.loggedIn)

const showLoginDialog = ref(false)
const showLogoutDialog = ref(false)
const showResetDialog = ref(false)
const dismissedDefaultWarning = ref(false)

const loginUsername = ref('')
const loginPassword = ref('')
const canSubmitLogin = computed(() => loginUsername.value.length > 0 && loginPassword.value.length > 0)

function handleLogin(): void {
  mqttStore.login(loginUsername.value, loginPassword.value)
}

function reloadPage(): void {
  location.reload()
}

watch(showLoginDialog, (open) => {
  if (!open) {
    loginUsername.value = ''
    loginPassword.value = ''
  }
})

const resetUsername = ref('')
const resetToken = ref('')
const resetNewPassword = ref('')
const resetConfirmPassword = ref('')
const tokenRequested = ref(false)
const resetRequested = ref(false)
const resetStatusMessage = ref('')

const canSubmitReset = computed(
  () =>
    resetUsername.value.length > 0 &&
    resetToken.value.length > 0 &&
    resetNewPassword.value.length > 0 &&
    resetNewPassword.value === resetConfirmPassword.value &&
    !resetRequested.value,
)

function requestToken(): void {
  tokenRequested.value = true
  mqttStore.requestPasswordResetToken(resetUsername.value)
  resetStatusMessage.value = `Falls der Benutzer "${resetUsername.value}" existiert und eine E-Mail-Adresse hinterlegt ist, wurde ein Token per E-Mail versendet.`
}

function submitReset(): void {
  resetRequested.value = true
  mqttStore.resetUserPassword(resetUsername.value, resetToken.value, resetNewPassword.value)
  resetStatusMessage.value = `Falls der Benutzer "${resetUsername.value}" existiert und der Token korrekt ist, wurde das Kennwort zurückgesetzt.`
}

watch(showResetDialog, (open) => {
  if (!open) {
    resetUsername.value = ''
    resetToken.value = ''
    resetNewPassword.value = ''
    resetConfirmPassword.value = ''
    tokenRequested.value = false
    resetRequested.value = false
    resetStatusMessage.value = ''
  }
})

// security topics only arrive after connecting - re-check whenever they do. A plain assignment,
// not just a one-way "open" guard: if anonymousAccessAllowed flips true after this already forced
// the dialog open (the topics can race in either order), it must also close again on its own -
// the modal's own backdrop/X close is separately suppressed above via the @update:model-value guard.
watchEffect(() => {
  showLoginDialog.value = userManagementActive.value && !anonymousAccessAllowed.value && !mqttStore.loggedIn
})
</script>
