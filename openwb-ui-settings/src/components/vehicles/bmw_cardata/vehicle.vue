<template>
  <div class="vehicle-soc-bmw-cardata">
    <openwb-base-alert v-if="isConnected" subtype="success">
      <b>BMW verbunden</b><br />
      Tokens vorhanden. BMW CarData kann genutzt werden.
    </openwb-base-alert>

    <openwb-base-alert v-else subtype="warning">
      <b>Nicht verbunden</b><br />
      Bitte BMW-Kopplung durchführen.
    </openwb-base-alert>

    <openwb-base-text-input
      title="Client ID"
      subtype="text"
      required
      :model-value="vehicle.configuration.client_id"
      @update:model-value="updateConfiguration($event, 'configuration.client_id')"
    >
      <template #help>
        BMW CarData Client ID aus dem BMW Portal.
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
        Fahrzeug-Identifikationsnummer (17 Zeichen).
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

    <openwb-base-alert v-if="isConnected" subtype="info">
      Die BMW-Verbindung ist aktiv. Eine erneute Kopplung ist nur nötig wenn die Verbindung verloren gegangen ist.
    </openwb-base-alert>

    <openwb-base-button-group-input
      title="BMW Auth"
      :buttons="[
        { buttonValue: 'start', text: 'BMW koppeln', class: 'btn-outline-primary' }
      ]"
      :model-value="null"
      @update:model-value="handleAuthAction"
    >
      <template #help>
        Startet die BMW-Kopplung. Nur nötig bei erstmaliger Einrichtung oder wenn die Verbindung verloren gegangen ist.
      </template>
    </openwb-base-button-group-input>

    <openwb-base-alert v-if="authStatus.user_code" subtype="info">
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
      • BMW CarData API: max. 50 Abfragen pro Tag<br />
      • Empfohlenes Intervall während Ladung: 30-60 Minuten<br />
      • Empfohlenes Intervall ohne Ladung: 720 Minuten
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
  },
  beforeUnmount() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  },
  methods: {
    async handleAuthAction(action) {
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

        // Auth-Daten im Broker speichern
        this.updateConfiguration(data.device_code || "", "configuration.auth_device_code");
        this.updateConfiguration(data.code_verifier || "", "configuration.auth_code_verifier");
        this.updateConfiguration(data.expires_at || 0, "configuration.auth_expires_at");
        this.updateConfiguration(false, "configuration.auth_connected");

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
        // Auth-Daten aus Broker an PHP senden
        const response = await fetch("/openWB/web/bmw_cardata/bmw_cardata_auth_status.php", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          cache: "no-store",
          body: JSON.stringify({
            client_id:     this.vehicle.configuration.client_id,
            device_code:   this.vehicle.configuration.auth_device_code,
            code_verifier: this.vehicle.configuration.auth_code_verifier,
            expires_at:    this.vehicle.configuration.auth_expires_at,
          }),
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

          // Tokens + Auth-Cleanup im Broker speichern
          this.updateConfiguration(data.access_token, "configuration.access_token");
          this.updateConfiguration(data.refresh_token || "", "configuration.refresh_token");
          this.updateConfiguration(data.expires_at || 0, "configuration.expires_at");
          this.updateConfiguration("", "configuration.container_id");
          this.updateConfiguration("", "configuration.auth_device_code");
          this.updateConfiguration("", "configuration.auth_code_verifier");
          this.updateConfiguration(0, "configuration.auth_expires_at");
          this.updateConfiguration(true, "configuration.auth_connected");

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

      } catch {
        this.authStatus.error = "Auth-Status konnte nicht geladen werden.";
        clearInterval(this.pollTimer);
        this.pollTimer = null;
      }
    },
  },
};
</script>
