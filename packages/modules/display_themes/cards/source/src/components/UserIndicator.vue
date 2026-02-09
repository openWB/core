<script>
/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faCircleUser as fasCircleUser,
  faArrowRightToBracket as fasArrowRightToBracket,
  faArrowRightFromBracket as fasArrowRightFromBracket,
  faEye as fasEye,
  faEyeSlash as fasEyeSlash,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasCircleUser, fasArrowRightToBracket, fasArrowRightFromBracket, fasEye, fasEyeSlash);
import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "UserIndicator",
  components: {
    FontAwesomeIcon,
  },
  props: {},
  data() {
    return {
      mqttStore: useMqttStore(),
      username: null,
      showLoginModal: false,
      showLogoutModal: false,
      loginUser: "",
      loginPassword: "",
      showPassword: false,
    };
  },
  computed: {
    loggedInUser() {
      return this.$cookies.get("mqtt")?.split(":")[0] || null;
    },
    /**
     * Check if user management is active
     * Defaults to true if the value is not set as this may be due to insufficient permissions
     * @returns boolean
     */
    userManagementActive() {
      return this.mqttStore.topics["openWB/system/security/user_management_active"] !== false;
    },
    accessAllowed() {
      return this.mqttStore.getAccessAllowed;
    },
    anonymousAccessAllowed() {
      return this.accessAllowed && this.loggedInUser === null;
    },
    enableLogin() {
      return this.loginUser.trim() !== "" && this.loginPassword.trim() !== "";
    },
    hideLogin() {
      return this.mqttStore.settings.hideLogin === true;
    },
  },
  mounted() {},
  methods: {
    dummy(event) {
      // dummy method to suppress vue warning about missing method in modal
      console.info("dummy method called with event:", event);
    },
    handleLogin(doLogin) {
      console.info("handleLogin called with value:", doLogin);
      this.showLoginModal = false;
      if (doLogin && this.loginUser.trim() !== "" && this.loginPassword.trim() !== "") {
        this.$cookies.set("mqtt", this.loginUser.trim() + ":" + this.loginPassword.trim());
        window.location.reload();
      } else {
        this.loginUser = "";
        this.loginPassword = "";
      }
    },
    handleLogout(doLogout) {
      console.info("handleLogout called with value:", doLogout);
      this.showLogoutModal = false;
      if (doLogout) {
        this.$cookies.remove("mqtt");
        // reload current location without # part
        const currentLocation = window.location.href.split("#")[0];
        window.history.replaceState({}, document.title, currentLocation);
        window.location.reload();
      }
    },
  },
};
</script>

<template>
  <i-button
    v-if="userManagementActive && !hideLogin"
    class="_padding-left:0 _padding-right:0 _margin-bottom:1"
    size="lg"
    block
    :title="loggedInUser ? `${loggedInUser} Abmelden` : 'Anmelden'"
    :color="loggedInUser ? 'success' : 'danger'"
    @click="loggedInUser ? showLogoutModal = true : showLoginModal = true"
  >
    <div class="buttonContent">
      <FontAwesomeIcon
        v-if="loggedInUser"
        :icon="['fas', 'circle-user']"
        class="_flex-shrink:0"
        size="lg"
      />
      <div
        class="username"
      >
        {{ loggedInUser || 'Anmelden' }}
      </div>
      <FontAwesomeIcon
        class="text-light px-2 _flex-shrink:0"
        :icon="loggedInUser ? ['fas', 'arrow-right-from-bracket'] : ['fas', 'arrow-right-to-bracket']"
        size="lg"
      />
    </div>
  </i-button>
  <!-- modals -->
  <Teleport to="body">
    <i-modal
      v-model="showLoginModal"
      class="modal-vehicle-select"
      size="lg"
    >
      <template #header>
        <FontAwesomeIcon
          class="text-light clickable px-2"
          :icon="['fas', 'arrow-right-to-bracket']"
          size="lg"
        />
        Anmelden
      </template>
      <template #footer>
        <i-row around>
          <i-button
            :disabled="!enableLogin"
            :outline="!enableLogin"
            color="success"
            @click="handleLogin(true)"
          >
            Anmelden
          </i-button>
          <i-button
            color="secondary"
            @click="handleLogin(false)"
          >
            Abbrechen
          </i-button>
        </i-row>
      </template>
      <i-form>
        <i-form-group>
          <i-row class="_margin-bottom:1">
            <i-column>
              <i-input
                v-model="loginUser"
                size="lg"
                placeholder="Benutzer"
              >
                <template #prepend>
                  <span>
                    <FontAwesomeIcon
                      :icon="['fas', 'circle-user']"
                      size="lg"
                    />
                  </span>
                </template>
              </i-input>
            </i-column>
          </i-row>
          <i-row>
            <i-column>
              <i-input
                v-model="loginPassword"
                size="lg"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Passwort"
              >
                <template #prepend>
                  <span>
                    <FontAwesomeIcon
                      :icon="['fas', 'lock']"
                      size="lg"
                    />
                  </span>
                </template>
                <template #suffix>
                  <FontAwesomeIcon
                    :icon="['fas', showPassword ? 'eye' : 'eye-slash']"
                    size="lg"
                    @click="showPassword = !showPassword"
                  />
                </template>
              </i-input>
            </i-column>
          </i-row>
        </i-form-group>
      </i-form>
    </i-modal>
    <i-modal
      v-model="showLogoutModal"
      class="modal-vehicle-select"
      size="lg"
    >
      <template #header>
        <FontAwesomeIcon
          class="text-light clickable px-2"
          :icon="['fas', 'arrow-right-from-bracket']"
          size="lg"
        />
        Abmelden
      </template>
      <template #footer>
        <i-row around>
          <i-button
            color="success"
            @click="handleLogout(true)"
          >
            Abmelden
          </i-button>
          <i-button
            color="secondary"
            @click="handleLogout(false)"
          >
            Abbrechen
          </i-button>
        </i-row>
      </template>
      <!-- logout form content goes here -->
      <p>
        Willst Du Dich wirklich abmelden?
      </p>
    </i-modal>
  </Teleport>
</template>

<style scoped>
.buttonContent {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.username {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
