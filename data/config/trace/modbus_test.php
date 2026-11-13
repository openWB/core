<!DOCTYPE html>
<html lang="de">

<head>
	<title>Modbus-Test</title>
	<meta charset="UTF-8">
</head>

<body>
	<pre><?php
			if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
				error_log('Diese Seite muss als HTTP-POST aufgerufen werden.');
				exit('Diese Seite muss als HTTP-POST aufgerufen werden.');
			}

			$host = escapeshellarg($_POST['host']);
			$port = escapeshellarg($_POST['port']);
			$start = escapeshellarg($_POST['start']);
			$length = escapeshellarg($_POST['length']);
			$modbus_id = escapeshellarg($_POST['id']);
			$data_type = escapeshellarg($_POST['data_type']);
			$function_code = escapeshellarg($_POST['function']);

			$base_dir = $_SERVER['DOCUMENT_ROOT'] . '/openWB';
			$command = 'PYTHONPATH=' . escapeshellarg($base_dir . '/packages') . ' /bin/bash ' .
				escapeshellarg($base_dir . '/runs/run_python.sh') . ' ' .
				escapeshellarg($base_dir . '/packages/tools/modbus_tester.py');
			$output = shell_exec(join(" ", [$command, $host, $port, $modbus_id, $start, $length, $data_type, $function_code]));
			echo htmlspecialchars($output);
			?></pre>
</body>

</html>
