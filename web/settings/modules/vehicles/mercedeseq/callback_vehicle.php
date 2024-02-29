<html>

<head>
	<meta charset="utf-8" />
</head>

<body>
	<?php
	//Callback procedure for mercedes SoC API EV
	if ($_GET["code"]) {
		$command = $_SERVER['DOCUMENT_ROOT'] . "/openWB/packages/modules/vehicles/mercedeseq/auth.py";

		$state = escapeshellarg($_GET['state']);
		$code = escapeshellarg($_GET['code']);

		$port = ($_SERVER['SERVER_PORT'] != 80 && $_SERVER['SERVER_PORT'] != 443) ? ':' . $_SERVER['SERVER_PORT'] : '';
		$callback_url = $_SERVER['REQUEST_SCHEME'] . "://" . $_SERVER['HTTP_HOST'] . $port . $_SERVER['SCRIPT_NAME'];

		$system_command = join(" ", [$command, $state, $code, $callback_url]);
		system($system_command);
	} else {
		echo "<p>" . $_GET["error"] . "</p>";
		echo "<p>" . $_GET["error_description"] . "</p>";
	}
	?>
</body>

</html>
