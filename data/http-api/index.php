<?php
if (isset($_GET["topic"])) {
	$topic = $_GET["topic"];
}
if (isset($_POST["topic"])) {
	$topic = $_POST["topic"];
}
if ( strlen($topic) < 3 ) {
	echo 'Topic is needed! Please obtain - topic - via GET or POST Request, f.e. http://IP:8080/?topic"openWB/system/time" or https://IP:8443/?topic"openWB/system/time"';
	exit();
}
$response = exec("timeout 1 mosquitto_sub -t $topic -C 1");
if (strlen($response) < 1) {
	$response = "Topic - $topic - nicht gefunden";
}
echo "$response";
?>
