<template>
  <div class="vehicle-soc-bmw-cardata">
    <openwb-base-alert v-if="vehicle.configuration.test_mode" subtype="info">
      <b>Testmodus aktiv</b><br />
      Es werden keine BMW-API-Abfragen ausgeführt.<br />
      SoC und Reichweite kommen aus den Testwerten.
    </openwb-base-alert>

    <openwb-base-alert v-else-if="isConnected" subtype="success">
      <b>BMW verbunden</b><br />
      Tokens vorhanden. BMW CarData kann genutzt werden.
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
      @update:model-value="updateConfiguration($event, 'configuration.test_mode')"
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
        <span v-if="isConnected"><b>Verbunden</b></span>
        <span v-else><b>Nicht verbunden</b></span>
        <br />
        <span v-if="authStatus.message">{{ authStatus.message }}</span>
      </openwb-base-alert>

      <openwb-base-button-group-input
        title="BMW Auth"
        :buttons="[
          { buttonValue: 'start', text: 'BMW koppeln', class: 'btn-outline-primary' },
          { buttonValue: 'refresh', text: 'Status aktualisieren', class: 'btn-outline-secondary' }
        ]"
        :model-value="null"
        @update:model-value="handleAuthAction"
      >
        <template #help>
          Startet die BMW-Kopplung oder aktualisiert den Verbindungsstatus.
        </template>
      </openwb-base-button-group-input>

      <openwb-base-alert v-if="authStatus.user_code && !isConnected" subtype="info">
        <b>BMW Auth läuft</b><br />
        URL: {{ authStatus.verification_uri }}<br />
        Code: <b>{{ authStatus.user_code }}</b>
      </openwb-base-alert>

      <openwb-base-alert v-if="authStatus.justConnected" subtype="success">
        <b>BMW erfolgreich verbunden!</b><br />
        Bitte jetzt auf <b>"Speichern"</b> klicken um die Verbindung dauerhaft zu sichern.
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
      • Live-Modus (mit Container-ID) ≈ 1 Call pro Abfrage<br />
      • Bei Token-Refresh kurzzeitig mehr Calls möglich<br />
      • Token läuft ab am: {{ tokenExpiry }}
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
        message: "",
        user_code: "",
        verification_uri: "",
        error: "",
        justConnected: false,
      },
      pollTimer: null,
    };
  },
  computed: {
    isConnected() {
      return !!this.vehicle.configuration.access_token;
    },
    tokenExpiry() {
      const expires_at = this.vehicle.configuration.expires_at;
      if (!expires_at) return "unbekannt";
      const date = new Date(expires_at * 1000);
      return date.toLocaleString("de-DE");
    },
  },
  beforeUnmount() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  },
  methods: {
    async handleAuthAction(action) {
      if (action === "refresh") {
        this.authStatus.message = this.isConnected ? "BMW verbunden." : "Keine gültige Verbindung hinterlegt.";
        this.authStatus.error = "";
        this.authStatus.justConnected = false;
        return;
      }
      if (action === "start") {
        if (!this.vehicle.configuration.client_id) {
          this.authStatus.error = "Bitte zuerst die Client ID eintragen und speichern.";
          return;
        }
        this.startAuth();
      }
    },

    async startAuth() {
      this.authStatus = { message: "Auth wird gestartet...", user_code: "", verification_uri: "", error: "", justConnected: false };

      try {
        const response = await fetch("/openWB/web/bmw_cardata/bmw_cardata_auth_start.php", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ client_id: this.vehicle.configuration.client_id }),
        });
        const data = await response.json();

        if (data.error) {
          this.authStatus.error = data.error;
          return;
        }

        this.authStatus = {
          message: data.message || "",
          user_code: data.user_code || "",
          verification_uri: data.verification_uri || "",
          error: "",
          justConnected: false,
        };

        if (data.user_code && !this.pollTimer) {
          this.pollTimer = setInterval(() => this.pollAuthStatus(), 5000);
        }
      } catch {
        this.authStatus.error = "BMW Auth konnte nicht gestartet werden.";
      }
    },

    async pollAuthStatus() {
      try {
        const response = await fetch("/openWB/web/bmw_cardata/bmw_cardata_auth_status.php", {
          cache: "no-store",
        });
        const data = await response.json();

        if (data.error) {
          this.authStatus.error = data.error;
          this.authStatus.message = "";
          clearInterval(this.pollTimer);
          this.pollTimer = null;
          return;
        }

        if (data.connected && data.access_token) {
          clearInterval(this.pollTimer);
          this.pollTimer = null;

          // Tokens in Konfiguration speichern
          this.updateConfiguration(data.access_token, "configuration.access_token");
          this.updateConfiguration(data.refresh_token || "", "configuration.refresh_token");
          this.updateConfiguration(data.expires_at || 0, "configuration.expires_at");
          this.updateConfiguration("", "configuration.container_id");

          this.authStatus = {
            message: "",
            user_code: "",
            verification_uri: "",
            error: "",
            justConnected: true,
          };
          return;
        }

        this.authStatus.message = data.message || "Warte auf BMW-Bestätigung...";
        this.authStatus.user_code = data.user_code || this.authStatus.user_code;
        this.authStatus.verification_uri = data.verification_uri || this.authStatus.verification_uri;

      } catch {
        this.authStatus.error = "Auth-Status konnte nicht geladen werden.";
        clearInterval(this.pollTimer);
        this.pollTimer = null;
      }
    },
  },
};
</script>
