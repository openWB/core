import mqtt from "mqtt";
import "./style.css";

const THEME_TOPIC_NAME = "openWB/optional/int_display/theme";
const VALID_PROTOCOLS = new Set(["http:", "https:"]);
const MESSAGE_TIMEOUT_MS = 20000;
const messageElement = document.getElementById("message");
let messageTimeoutHandle;
let hasProcessedValidUrl = false;

function setStatus(message) {
  if (messageElement) {
    messageElement.textContent = message;
  }
}

function parseThemePayload(payload) {
  try {
    return JSON.parse(payload.toString());
  } catch (error) {
    setStatus("Fehler beim Lesen der Konfiguration.");
    return null;
  }
}

function normalizeUrl(inputUrl) {
  const trimmedUrl = typeof inputUrl === "string" ? inputUrl.trim() : "";
  if (!trimmedUrl) {
    return "";
  }
  if (/^https?:\/\//i.test(trimmedUrl)) {
    return trimmedUrl;
  }
  return `http://${trimmedUrl}`;
}

function formatConfiguredValue(inputUrl) {
  const value = typeof inputUrl === "string" ? inputUrl.trim() : "";
  return value || "<leer>";
}

function validateUrl(candidateUrl, configuredValue) {
  if (!candidateUrl) {
    setStatus(`Fehler: Keine URL in der Theme-Konfiguration gefunden (Wert: ${configuredValue}).`);
    return null;
  }

  let parsedUrl;
  try {
    parsedUrl = new URL(candidateUrl);
  } catch (error) {
    setStatus(`Fehler: Ungültige URL in der Konfiguration (Wert: ${configuredValue}).`);
    return null;
  }

  if (!VALID_PROTOCOLS.has(parsedUrl.protocol)) {
    setStatus(`Fehler: Nur http:// und https:// URLs sind erlaubt (Wert: ${configuredValue}).`);
    return null;
  }

  const hostname = parsedUrl.hostname;
  const isLocalhost = hostname === "localhost";
  const isIpv4 = /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/.test(hostname);
  const normalizedHostname = hostname.replace(/^\[/, "").replace(/\]$/, "");
  const isIpv6 = normalizedHostname.includes(":") && /^[0-9a-f:]+$/i.test(normalizedHostname);
  const hasDotInHostname = hostname.includes(".");

  if (!isLocalhost && !isIpv4 && !isIpv6 && !hasDotInHostname) {
    setStatus(`Fehler: Ungültiger Hostname in der URL-Konfiguration (Wert: ${configuredValue}).`);
    return null;
  }

  return parsedUrl.toString();
}

function startMessageTimeout() {
  clearTimeout(messageTimeoutHandle);
  messageTimeoutHandle = setTimeout(() => {
    if (!hasProcessedValidUrl) {
      setStatus("Warte auf gültige URL-Konfiguration...");
    }
  }, MESSAGE_TIMEOUT_MS);
}

function createClient() {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const port = parseInt(location.port, 10) || (location.protocol === "https:" ? 443 : 80);
  const connectUrl = `${protocol}://${location.hostname}:${port}/ws`;

  return mqtt.connect(connectUrl, {
    connectTimeout: 4000,
    reconnectPeriod: 4000,
    clean: false,
    clientId: Math.random().toString(36).replace(/[^a-z]+/g, "").substring(0, 8),
  });
}

const client = createClient();

client.on("connect", () => {
  setStatus("Verbunden. Lade Konfiguration...");
  client.subscribe(THEME_TOPIC_NAME, { qos: 0 });
  startMessageTimeout();
});

client.on("reconnect", () => {
  setStatus("MQTT-Verbindung verloren. Verbinde erneut...");
});

client.on("close", () => {
  if (!client.connected) {
    setStatus("MQTT-Verbindung geschlossen. Verbinde erneut...");
  }
});

client.on("error", () => {
  setStatus("MQTT-Verbindungsfehler. Versuche erneut...");
});

client.on("message", (topic, payload) => {
  if (topic !== THEME_TOPIC_NAME) {
    return;
  }

  const theme = parseThemePayload(payload);
  if (!theme || !theme.configuration) {
    setStatus("Fehler: Keine URL in der Theme-Konfiguration gefunden.");
    hasProcessedValidUrl = false;
    startMessageTimeout();
    return;
  }

  const configuredValue = formatConfiguredValue(theme.configuration.url);
  const normalizedUrl = normalizeUrl(theme.configuration.url);
  const validatedUrl = validateUrl(normalizedUrl, configuredValue);
  if (!validatedUrl) {
    hasProcessedValidUrl = false;
    startMessageTimeout();
    return;
  }

  hasProcessedValidUrl = true;
  clearTimeout(messageTimeoutHandle);
  setStatus(`Lade URL: ${validatedUrl}`);
  window.location.href = validatedUrl;
});
