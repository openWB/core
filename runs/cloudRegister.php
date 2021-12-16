<?php
$debug = false;

if ($argc > 1) {
	debugPrint($argv[1]);
	$data = json_decode($argv[1], true);
	debugPrint($data["username"] . ": " . $data["email"]);
} else {
	abort("No credentials provided!");
}

function debugPrint($message){
	global $debug;
	if( $debug ){
		echo $message . "\n";
	}
}

function abort($message){
	echo $message . "\n";
	exit(1);
}

# Create a connection
$url = 'https://web.openwb.de/php/localregistrate.php';
$ch = curl_init($url);
# Form data string
$postData = [ "username" => $data["username"], "email" => $data["email"] ];
$postString = http_build_query($postData)."\n";
debugPrint($postString);
# Setting our options
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $postString);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
# Get the response
$response = curl_exec($ch);
curl_close($ch);

if ( $response == "nomail" ) {
	abort("Keine gültige Email angegeben.");
} elseif ( $response == "maildoesnotexist" ) {
	abort("Keine Email angegeben.");
} elseif ( $response == "usernamenotvalid" ) {
	abort("Ungültiger Benutzername.");
} elseif ( $response == "usernameempty" ) {
	abort("Kein Benutzername angegeben.");
} elseif ( $response == "exists" ) {
	abort("Der Benutzername existiert bereits.");
} else {
	debugPrint($response);
	$upass = explode(',', $response);
	$resultData = array("username" => $upass[0], "password" => $upass[1]);
	echo json_encode($resultData) . "\n";
}
?>
