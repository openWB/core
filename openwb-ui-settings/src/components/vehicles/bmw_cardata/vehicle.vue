<template>
  <div class="vehicle-soc-bmw-cardata">
    <openwb-base-alert v-if="vehicle.configuration.test_mode" subtype="info">
      <b>Testmodus aktiv</b><br />
      Es werden keine BMW-API-Abfragen ausgeführt.<br />
      SoC und Reichweite kommen aus den Testwerten.
    </openwb-base-alert>

    <openwb-base-alert
      v-else-if="authStatus.connected"
      subtype="success"
    >
      <b>BMW verbunden</b><br />
      Tokens vorhanden. BMW CarData kann genutzt werden.
      <template v-if="authStatus.message">
        <br />
        {{ authStatus.message }}
      </template>
    </openwb-base-alert>

    <openwb-base-alert
      v-else-if="authStatus.user_code"
      subtype="info"
    >
      <b>BMW Auth läuft</b><br />
      BMW-Seite öffnen und Code bestätigen.<br />
      <span v-if="authStatus.verification_uri">
        URL:
        <a :href="authStatus.verification_uri" target="_blank" rel="noopener noreferrer">
          {{ authStatus.verification_uri }}
        </a>
        <br />
      </span>
      Code: <b>{{ authStatus.user_code }}</b>
      <template v-if="authStatus.message">
        <br />
        {{ authStatus.message }}
      </template>
    </openwb-base-alert>

    <openwb-base-alert v-else subtype="warning">
      <b>Live-Modus aktiv</b><br />
      Aktuell ist keine gültige BMW-Verbindung hinterlegt oder der Status ist noch unbekannt.
    </openwb-base-alert>

    <openwb-base-button-group-input
      title="Testmodus aktiv"
      :buttons="[
        { buttonValue: true, text: 'Ja', class: 'btn-outline-success' },
        { buttonValue: false, text: 'Nein', class: 'btn-outline-danger' }
      ]"
      :model-value="vehicle.configuration.test_mode"
      @update:model-value="handleTestModeChange"
    >
      <template #help>
        Im Testmodus werden keine BMW-Daten abgefragt.
      </template>
    </openwb-base-button-group-input>

    <template v-if="vehicle.configuration.test_mode">
      <openwb-base-number-input
        title="Test SoC"
        unit="%"
        :min="0"
        :max="100"
        :model-value="vehicle.configuration.test_soc"
        @update:model-value="updateConfiguration($event, 'configuration.test_soc')"
      >
        <template #help>
          Simulierter Ladezustand (0–100 %).
        </template>
      </openwb-base-number-input>

      <openwb-base-number-input
        title="Test Reichweite"
        unit="km"
        :min="0"
        :model-value="vehicle.configuration.test_range"
        @update:model-value="updateConfiguration($event, 'configuration.test_range')"
      >
        <template #help>
          Simulierte Reichweite in km.
        </template>
      </openwb-base-number-input>
    </template>

    <template v-else>
      <openwb-base-text-input
        title="Client ID"
        subtype="text"
        required
        :model-value="vehicle.configuration.client_id"
        @update:model-value="updateConfiguration($event, 'configuration.client_id')"
      >
        <template #help>
          BMW CarData Client ID.
        </template>
      </openwb-base-text-input>

      <openwb-base-text-input
        title="VIN"
        subtype="text"
        required
        :model-value="vehicle.configuration.vin"
        @update:model-value="updateConfiguration($event, 'configuration.vin')"
      >
        <template #help>
          Fahrzeug-VIN (FIN).
        </template>
      </openwb-base-text-input>

      <openwb-base-alert subtype="secondary">
        <b>BMW Verbindung</b><br />
        Status:
        <span v-if="isLoadingStatus"><b>Wird geprüft…</b></span>
        <span v-else-if="authStatus.connected"><b>Verbunden</b></span>
        <span v-else-if="authStatus.user_code"><b>Authentifizierung läuft</b></span>
        <span v-else><b>Nicht verbunden</b></span>
        <template v-if="authStatus.message">
          <br />
          {{ authStatus.message }}
        </template>
      </openwb-base-alert>

      <openwb-base-button-group-input
        title="BMW Auth"
        :buttons="authButtons"
        :model-value="null"
        @update:model-value="handleAuthAction"
      >
        <template #help>
          Startet die BMW-Kopplung oder aktualisiert den Verbindungsstatus.
        </template>
      </openwb-base-button-group-input>

      <openwb-base-alert v-if="statusInfo" subtype="secondary">
        <b>Statusinfo</b><br />
        {{ statusInfo }}
      </openwb-base-alert>

      <openwb-base-alert v-if="authStatus.error" subtype="danger">
        <b>Fehler</b><br />
        {{ authStatus.error }}
      </openwb-base-alert>
    </template>

    <openwb-base-button-group-input
      title="SoC während der Ladung berechnen"
      :buttons="[
        { buttonValue: false, text: 'Nein', class: 'btn-outline-danger' },
        { buttonValue: true, text: 'Ja', class: 'btn-outline-success' }
      ]"
      :model-value="vehicle.configuration.calculate_soc"
      @update:model-value="updateConfiguration($event, 'configuration.calculate_soc')"
    >
      <template #help>
        openWB berechnet den Ladestand während der Ladung selbst.
      </template>
    </openwb-base-button-group-input>

    <openwb-base-alert subtype="secondary">
      <b>Technische Hinweise:</b><br />
      • Testmodus = 0 BMW-API-Calls<br />
      • Auth-Status prüft nur die lokale Verbindung / Tokens<br />
      • Live-Modus (mit Container-ID) ≈ 1 BMW-Call pro SoC-Abfrage<br />
      • Bei Token-Refresh kurzzeitig zusätzlicher OAuth-Call möglich
    </openwb-base-alert>
  </div>
</template>

<script>
import VehicleConfigMixin from "../VehicleConfigMixin.vue";

export default {
  name: "VehicleSocBmwCardata",
  mixins: [VehicleConfigMixin],
  data() {
    return {
      authStatus: {
        connected: false,
        message: "",
        user_code: "",
        verification_uri: "",
        error: "",
      },
      pollTimer: null,
      isLoadingStatus: false,
      isStartingAuth: false,
      lastStatusCheckFailed: false,
    };
  },
  computed: {
    authButtons() {
      return [
        {
          buttonValue: "start",
          text: this.isStartingAuth ? "BMW koppeln läuft…" : "BMW koppeln",
          class: "btn-outline-primary",
        },
        {
          buttonValue: "refresh",
          text: this.isLoadingStatus ? "Status wird geladen…" : "Status aktualisieren",
          class: "btn-outline-secondary",
        },
      ];
    },
    statusInfo() {
      if (this.isStartingAuth) {
        return "BMW Auth wird gestartet…";
      }
      if (this.isLoadingStatus) {
        return "Verbindungsstatus wird geprüft…";
      }
      if (this.lastStatusCheckFailed) {
        return "Letzte Statusprüfung war nicht erfolgreich.";
      }
      return "";
    },
  },
  mounted() {
    if (!this.vehicle.configuration.test_mode) {
      this.loadAuthStatus();
    }
  },
  beforeUnmount() {
    this.stopPolling();
  },
  methods: {
    handleTestModeChange(value) {
      this.updateConfiguration(value, "configuration.test_mode");

      if (value) {
        this.stopPolling();
        this.resetAuthUiState();
      } else {
        this.loadAuthStatus();
      }
    },

    resetAuthUiState() {
      this.authStatus = {
        connected: false,
        message: "",
        user_code: "",
        verification_uri: "",
        error: "",
      };
      this.isLoadingStatus = false;
      this.isStartingAuth = false;
      this.lastStatusCheckFailed = false;
    },

    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer);
        this.pollTimer = null;
      }
    },

    startPolling() {
      if (!this.pollTimer) {
        this.pollTimer = setInterval(() => {
          this.loadAuthStatus({ silent: true });
        }, 5000);
      }
    },

    applyAuthStatus(data) {
      this.authStatus = {
        connected: !!data.connected,
        message: data.message || "",
        user_code: data.user_code || "",
        verification_uri: data.verification_uri || "",
        error: data.error || "",
      };

      if (this.authStatus.connected) {
        this.stopPolling();
      } else if (this.authStatus.user_code) {
        this.startPolling();
      } else {
        this.stopPolling();
      }
    },

    async parseJsonResponse(response, endpointName) {
      const rawText = await response.text();

      if (!response.ok) {
        throw new Error(
          `${endpointName} lieferte HTTP ${response.status}: ${rawText || "keine Antwort"}`
        );
      }

      try {
        return rawText ? JSON.parse(rawText) : {};
      } catch (error) {
        throw new Error(
          `${endpointName} lieferte kein gültiges JSON. Antwort: ${rawText.substring(0, 500)}`
        );
      }
    },

    async loadAuthStatus(options = {}) {
      const { silent = false } = options;

      if (this.vehicle.configuration.test_mode) {
        this.stopPolling();
        return;
      }

      if (!silent) {
        this.isLoadingStatus = true;
      }

      this.lastStatusCheckFailed = false;

      try {
        const response = await fetch("/openWB/web/bmw_cardata/bmw_cardata_auth_status.php", {
          cache: "no-store",
        });

        const data = await this.parseJsonResponse(response, "Auth-Status");
        this.applyAuthStatus(data);
      } catch (error) {
        console.error("BMW auth status error:", error);
        this.stopPolling();
        this.lastStatusCheckFailed = true;
        this.authStatus = {
          connected: false,
          message: "",
          user_code: "",
          verification_uri: "",
          error: "Auth-Status konnte nicht geladen werden.",
        };
      } finally {
        if (!silent) {
          this.isLoadingStatus = false;
        }
      }
    },

    async handleAuthAction(action) {
      if (action === "refresh") {
        if (this.isLoadingStatus || this.isStartingAuth) {
          return;
        }
        await this.loadAuthStatus();
        return;
      }

      if (action !== "start") {
        return;
      }

      if (this.isStartingAuth || this.isLoadingStatus) {
        return;
      }

      if (!this.vehicle.configuration.client_id) {
        this.authStatus.error = "Bitte zuerst die Client ID eintragen und speichern.";
        return;
      }

      this.isStartingAuth = true;
      this.lastStatusCheckFailed = false;
      this.authStatus.error = "";

      try {
        const response = await fetch("/openWB/web/bmw_cardata/bmw_cardata_auth_start.php", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            client_id: this.vehicle.configuration.client_id,
          }),
        });

        const data = await this.parseJsonResponse(response, "BMW Auth Start");
        this.applyAuthStatus(data);

        if (!this.authStatus.connected) {
          await this.loadAuthStatus({ silent: true });
        }
      } catch (error) {
        console.error("BMW auth start error:", error);
        this.authStatus.error = "BMW Auth konnte nicht gestartet werden.";
      } finally {
        this.isStartingAuth = false;
      }
    },
  },
};
</script>