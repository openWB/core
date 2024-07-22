<?php
$sendmessage = 0;
if (isset($_GET["topic"])) {
	$topic = escapeshellarg($_GET["topic"]);
}
if (isset($_POST["topic"])) {
	$topic = escapeshellarg($_POST["topic"]);
}
if ( strlen($topic) < 3 ) {
	echo 'No topic given.';
	exit();
}
if (isset($_GET["msg"])) {
	$msg = escapeshellarg($_GET["msg"]);
	$sendmessage = 1;
}
if (isset($_POST["msg"])) {
	$msg = escapeshellarg($_POST["msg"]);
	$sendmessage = 1;
}
if ( $sendmessage === 1 ) {
	if ( strncmp($topic, "'openWB/set/", 12) === 0) {
		exec("mosquitto_pub -r -t $topic -m $msg", $output, $exitcode);
		if ( $exitcode > 0) {
			echo "failure: $output, code: $exitcode";
		} else {
			echo "{ topic: $topic , message: $msg, status: \"sent\" }";
		}
	}else {
		echo "{ topic: $topic , error: \"Topic not valid. Only openWB/set/ topics are writable.\" }"; 
	}

} else {
	$response = exec("timeout 1 mosquitto_sub -t $topic -C 1");
	if (strlen($response) < 1) {
		$topic=htmlentities($topic);
		$response = "{ topic: $topic , error: \"Topic not found.\" }";
	}
	echo "$response";

}
?>
