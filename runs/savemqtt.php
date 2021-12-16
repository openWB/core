<?php
$debug = false;

$bridgePrefix = "99-bridge-openwb";
// generate a random integer for our clientID
$randomnr = rand();
$mosquittoConfDir = "/etc/mosquitto/conf.d/";

if ($argc > 2) {
	$bridgeId = $argv[1];
	$configuration = json_decode($argv[2]);
} else {
	cleanAndExit("No id [1] and configuration [2] provided!");
}

function debugPrint($message){
	global $debug;
	if( $debug ){
		echo $message . "\n";
	}
}

function cleanAndExit($message){
	exit($message . "\n");
}

debugPrint("Bridge Id: '$bridgeId'");

$bridgeFileName = "${bridgePrefix}-${bridgeId}.conf";
debugPrint("Bridge root file name: '{$bridgeFileName}'");

if ($configuration == "" || $configuration->active != true) {
	// empty configuration tells us to delete the config file
	// also remove file if not active
	if (file_exists($mosquittoConfDir . $bridgeFileName)) {
		debugPrint("Konfigurationsdatei gefunden: '$mosquittoConfDir$bridgeFileName'");
		exec("sudo rm $mosquittoConfDir$bridgeFileName");
	} else {
		cleanAndExit("Keine Konfigurationsdatei für die Brücke mit ID $bridgeId gefunden: '$mosquittoConfDir$bridgeFileName'");
	}
} else {
	// generate new config file
	if ($configuration->name == "") {
		cleanAndExit("Bitte eine eindeutige Bezeichnung für die Verbindung vergeben.");
	}
	if(!preg_match('/^[a-zA-Z0-9]+$/', $configuration->name)) {
		cleanAndExit("Der Bezeichner für die Bridge ('" . htmlentities($configuration->name) . "') enthält ungültige Zeichen. Nur a-z, A-Z, 0-9 sind erlaubt.");
	}
	debugPrint("Bridge to configure: '{$configuration->name}'");

	//
	// validate input data and assign to variables
	//
	$fileToUseForNewConfig = "/tmp/$bridgeFileName";
	debugPrint("Bridge file name for new config: '$fileToUseForNewConfig'");

	if (!isset($configuration->remote->host) || empty($configuration->remote->host)) {
		cleanAndExit ("Die Address oder der Namen des entfernten MQTT-Servers ('" . htmlentities($configuration->remote->host) . "') ist ungültig oder nicht vorhanden.");
	}
	debugPrint("HostOrAddress {$configuration->remote->host}");

	if (!isset($configuration->remote->port) || empty($configuration->remote->port)) {
		$configuration->remote->port = 1886;
	}
	debugPrint("Port {$configuration->remote->port}");

	if ($configuration->remote->username == "") {
		cleanAndExit("Bitte einen Benutzernamen für den entfernten MQTT-Servers setzen.");
	}
	if (!preg_match('/^([a-zA-Z0-9_\-+.]+)$/', $configuration->remote->username)) {
		cleanAndExit("Der Bezeichner für den Benutzer auf dem entfernten MQTT-Servers ('" . htmlentities($configuration->remote->username) . "') enthält ungültige Zeichen. Nur a-z, A-Z, 0-9, Punkt, Unterstrich, Minus und Plus sind erlaubt.");
	}
	debugPrint("RemoteUser: {$configuration->remote->username}");

	if (!isset($configuration->remote->password) || empty($configuration->remote->password)) {
		cleanAndExit("Ungültiges Passwort: Nicht vorhanden oder leer.");
	}
	debugPrint("RemotePass: <vorhanden>");

	if (!preg_match('/^[a-zA-Z0-9_\-\/]+$/', $configuration->remote->prefix)) {
		cleanAndExit("Der Bezeichner für den Topic-Präfix auf dem entfernten MQTT-Server ('" . htmlentities($configuration->remote->prefix) . "') enthält ungültige Zeichen. Nur a-z, A-Z, 0-9, Unterstrich, Schrägstrich und Minus sind erlaubt.");
	}
	debugPrint("RemotePrefix: {$configuration->remote->prefix}");

	if (!preg_match('/^(mqttv31|mqttv311)$/', $configuration->remote->protocol)) {
		cleanAndExit("Interner Fehler: Ungültiges MQTT Protokoll '" . htmlentities($configuration->remote->protocol) . "'");
	}
	debugPrint("MQTT protocol: {$configuration->remote->protocol}");

	if (!preg_match('/^(auto|tlsv1.2|tlsv1.1|tlsv1.0)$/', $configuration->remote->tls_version)) {
		cleanAndExit("Interner Fehler: Ungültiges TLS Protokoll '" . htmlentities($configuration->remote->tls_version) . "'");
	}
	debugPrint("TLS version: {$configuration->remote->tls_version}");
	$tls_version_string = "bridge_tls_version " . $configuration->remote->tls_version;
	if ($configuration->remote->tls_version == "auto") {
		// do not force a tls version
		$tls_version_string = "# " . $tls_version_string;
	}

	if (!isset($configuration->remote->client_id) || ($configuration->remote->client_id !== "")){
		$configuration->remote->client_id = "openWB-$bridgeId";
	}
	debugPrint("Client ID: " . $configuration->remote->client_id);

	if (!isset($configuration->remote->try_private) || ($configuration->remote->try_private !== true)){
		$configuration->remote->try_private = false;
	}
	debugPrint("try_private: " . $configuration->remote->try_private);

	if (!isset($configuration->data_transfer->status) || ($configuration->data_transfer->status !== true)){
		$configuration->data_transfer->status = false;
	};

	if (!isset($configuration->data_transfer->graph) || ($configuration->data_transfer->graph !== true)){
		$configuration->data_transfer->graph = false;
	}

	if (!isset($configuration->data_transfer->configuration) || ($configuration->data_transfer->configuration !== true)){
		$configuration->data_transfer->configuration = false;
	}

	if (!$configuration->data_transfer->status && !$configuration->data_transfer->graph && !$configuration->data_transfer->configuration) {
		cleanAndExit("Es macht keinen Sinn eine MQTT-Brücke zu konfigurieren welche weder Daten publiziert noch Konfigurationen empfängt. Bitte mindestens eine Checkbox bei 'Zum entfernten Server weiterleiten' oder 'Konfiguration der openWB durch entfernten Server ermöglichen' aktivieren.");
	}

	//
	// create the new config file
	//
	$configFile = fopen($fileToUseForNewConfig, 'w');
	if (!$configFile) {
		cleanAndExit("Interner Fehler: Kann die Konfigurationsdatei für die Brücke nicht erzeugen.");
	}
	debugPrint("Opened '$fileToUseForNewConfig' and now writing configuration to it");

	fwrite($configFile, <<<EOS
	# bridge to {$configuration->remote->host}:{$configuration->remote->port}
	#

	# Just a name of subsequently configured the bridge.
	connection {$configuration->name}

	# The host name or IP address and port number of the remote MQTT server.
	address {$configuration->remote->host}:{$configuration->remote->port}


	###################################################################
	## Below choose what to share (bridge to) the remote MQTT server ##
	###################################################################

	EOS
	);

	if ($configuration->data_transfer->status) {
		fwrite($configFile, <<<EOS
	# export general data to remote
	topic openWB/general/# out 2 "" {$configuration->remote->prefix}

	# export system data to remote
	topic openWB/system/# out 2 "" {$configuration->remote->prefix}

	# export all counter data to remote
	topic openWB/counter/# out 2 "" {$configuration->remote->prefix}

	# export all charge point data to remote
	topic openWB/chargepoint/# out 2 "" {$configuration->remote->prefix}

	# export all battery data to remote
	topic openWB/bat/# out 2 "" {$configuration->remote->prefix}

	# export all pv data to remote
	topic openWB/pv/# out 2 "" {$configuration->remote->prefix}

	# export all vehicle data to remote
	topic openWB/vehicle/# out 2 "" {$configuration->remote->prefix}

	# export all optional data to remote
	topic openWB/optional/# out 2 "" {$configuration->remote->prefix}

	EOS
		);
	}

	if ($configuration->data_transfer->graph) {
		fwrite($configFile, <<<EOS
	# export graph data to remote
	topic openWB/graph/# out 2 "" {$configuration->remote->prefix}

	EOS
		);
	}

	fwrite($configFile, <<<EOS

	##################################################################################################
	## Below choose what to subscribe on  the remote MQTT server in order to receive setting data   ##
	## You may comment everything in order to not allow any MQTT remote configuration of the openWB ##
	##################################################################################################

	EOS
	);

	if ($configuration->data_transfer->configuration) {
		fwrite($configFile, <<<EOS
	topic openWB/set/# both 2 "" {$configuration->remote->prefix}

	EOS
		);
	}

	fwrite($configFile, <<<EOS

	##############################
	## Remote server settings   ##
	##############################

	# Client ID that appears in local MQTT server's log data.
	# Setting it might simplify debugging.
	local_clientid bridgeClient-{$configuration->name}

	# User name to for logging in to the remote MQTT server.
	remote_username {$configuration->remote->username}

	# Password for logging in to the remote MQTT server.
	remote_password {$configuration->remote->password}

	# Client ID that appears in remote MQTT server's log data.
	# Setting it might simplify debugging.
	# Commenting uses a random ID and thus gives more privacy.
	remote_clientid {$configuration->remote->client_id}-{$randomnr}

	# MQTT protocol to use - ideally leave at latest version (mqttv311).
	# Only change if remote doesn't support mqtt protocol version 3.11.
	bridge_protocol_version {$configuration->remote->protocol}

	# TLS version to use for transport encryption to the remote MQTT server.
	# Use at least tlsv1.2. Comment to not force a specific encryption.
	{$tls_version_string}

	# Verify TLS remote host name (false).
	# Only change if you know what you're doing!
	bridge_insecure false

	# Indicate to remote that we're a bridge. Only compatible with remote Mosquitto brokers.
	# Only change if you know what you're doing!
	try_private {$configuration->remote->try_private}

	# How often a "ping" is sent to the remote server to indicate that we're still alive and keep firewalls open.
	keepalive_interval 63

	# Path to a directory with the certificate for verifying TLS connections.
	# The default will work for official certificates (including LetsEncrypt ones).
	# Don't change unless you're using self-signed certificates.
	bridge_capath /etc/ssl/certs



	###################################################################
	## don't change below unless you _really_ know what you're doing ##
	###################################################################

	# Automatically connect to the remote MQTT server.
	# There a restart_timeout parameter which defaults to jitters with a base of 5 seconds and a cap of 30 seconds so the
	# local side doesn't get overloaded trying to reconnect to a non-available remote.
	start_type automatic

	notifications false
	cleansession false

	EOS
	);

	debugPrint("Now closing '$configFile' ('$fileToUseForNewConfig')");

	fclose($configFile);
	exec("sudo mv $fileToUseForNewConfig $mosquittoConfDir$bridgeFileName");
}

if (!$debug) {
	echo "Bitte die OpenWB neu starten, damit die Änderungen übernommen werden.\n";
	// restart or reload of broker in normal operation has several side effects and should be avoided!
	// exec("sudo service mosquitto restart");
}
?>
