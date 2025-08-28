<?php
// systeminfo_api.php
// This script provides system information in JSON format for API access and control.

$serviceList = [
	'openwb2.service',
	'openwbRemoteSupport.service',
	'mosquitto.service',
	'mosquitto_local.service'
];

$numTopProcesses = 10;

function getHardwareInfo()
{
	// Board-Name
	$board = trim(@shell_exec("cat /sys/class/dmi/id/board_name 2>/dev/null"));
	if ($board === '') {
		$board = trim(@shell_exec("cat /proc/device-tree/model 2>/dev/null"));
	}
	if ($board === '') {
		$board = 'unbekannt';
	}

	// CPU-Kerne
	$cpuCores = (int)@shell_exec('nproc') ?: 1;

	// CPU-Temperatur (verschiedene Pfade möglich)
	$temp = null;
	$paths = [
		'/sys/class/thermal/thermal_zone0/temp',
		'/sys/devices/virtual/thermal/thermal_zone0/temp'
	];
	foreach ($paths as $path) {
		if (is_readable($path)) {
			$raw = trim(file_get_contents($path));
			if (is_numeric($raw)) {
				// Wert meist in Milligrad
				$temp = round(((int)$raw) / 1000, 1);
				break;
			}
		}
	}
	if ($temp === null) {
		// Fallback: vcgencmd (z.B. Raspberry Pi)
		$vcgencmd = trim(@shell_exec('which vcgencmd'));
		if ($vcgencmd) {
			$out = trim(@shell_exec('vcgencmd measure_temp 2>/dev/null'));
			if (preg_match('/temp=([\d\.]+)/', $out, $m)) {
				$temp = (float)$m[1];
			}
		}
	}
	if ($temp === null) {
		$temp = 'unbekannt';
	}

	// Uptime
	$uptime = 'unbekannt';
	if (is_readable('/proc/uptime')) {
		$uptimeSeconds = (float)file_get_contents('/proc/uptime');
		$days = floor($uptimeSeconds / 86400);
		$hours = floor(($uptimeSeconds % 86400) / 3600);
		$minutes = floor(($uptimeSeconds % 3600) / 60);
		$seconds = floor($uptimeSeconds % 60);
		$uptime = sprintf('%d Tage, %02d:%02d:%02d', $days, $hours, $minutes, $seconds);
	}

	// Systemzeit
	$systemTime = date('d.m.Y, H:i:s');

	return [
		'board' => [
			'value' => $board,
			'unit' => ''
		],
		'cpu_cores' => [
			'value' => $cpuCores,
			'unit' => ''
		],
		'cpu_temp' => [
			'value' => $temp,
			'unit' => is_numeric($temp) ? '°C' : ''
		],
		'uptime' => [
			'value' => $uptime,
			'unit' => ''
		],
		'system_time' => [
			'value' => $systemTime,
			'unit' => ''
		]
	];
}

function getNetworkInfo()
{
	$mac = 'unbekannt';
	$ip = 'unbekannt';
	$subnet = 'unbekannt';
	$gateway = 'unbekannt';
	$iface = null;

	// Ermittle Gateway und zugehörige Schnittstelle
	$route = @shell_exec("ip route | awk '/default/ {print \$3, \$5; exit}'");
	if ($route) {
		list($gateway, $iface) = explode(' ', trim($route));
	}

	if ($iface) {
		// MAC-Adresse mit ip-Befehl
		$macInfo = @shell_exec("ip link show $iface | awk '/link\\// {print \$2; exit}'");
		if ($macInfo) {
			$mac = trim($macInfo);
		}
		// IP und Subnetz
		$ipInfo = @shell_exec("ip -o -f inet addr show $iface | awk '{print \$4}'");
		if ($ipInfo) {
			$ipCidr = trim($ipInfo);
			if (strpos($ipCidr, '/') !== false) {
				list($ip, $cidr) = explode('/', $ipCidr);
				// Subnetz berechnen
				$subnet = long2ip(-1 << (32 - (int)$cidr));
			}
		}
	}

	return [
		'interface' => [
			'value' => $iface ?? 'unbekannt',
			'unit' => ''
		],
		'mac' => [
			'value' => $mac,
			'unit' => ''
		],
		'ip' => [
			'value' => $ip,
			'unit' => ''
		],
		'subnet' => [
			'value' => $subnet,
			'unit' => ''
		],
		'gateway' => [
			'value' => $gateway,
			'unit' => ''
		]
	];
}

function getSoftwareInfo()
{
	$version = 'unbekannt';
	// $branch = 'unbekannt';
	$commit = 'unbekannt';

	// Git-Verzeichnis bestimmen (eine Ebene höher als "web")
	$repoDir = dirname(__DIR__, 2);

	// Lese Versionsdatei (eine Ebene höher)
	$versionFile = dirname(__DIR__, 1) . '/version';
	if (is_readable($versionFile)) {
		$version = trim(file_get_contents($versionFile));
	}

	// // Ermittle aktuellen Git-Branch
	// $branchCmd = 'git -C ' . escapeshellarg($repoDir) . ' rev-parse --abbrev-ref HEAD 2>/dev/null';
	// $branchOut = trim(@shell_exec($branchCmd));
	// if ($branchOut !== '') {
	// 	$branch = $branchOut;
	// }

	// Ermittle aktuellen Git-Commit
	$commitFile = dirname(__DIR__, 1) . '/lastcommit';
	if (is_readable($commitFile)) {
		$commit = trim(file_get_contents($commitFile));
	}

	return [
		'version' => [
			'value' => $version,
			'unit' => ''
		],
		// 'git_branch' => [
		// 	'value' => $branch,
		// 	'unit' => ''
		// ],
		'git_commit' => [
			'value' => $commit,
			'unit' => ''
		]
	];
}

function getCpuLoad()
{
	$load = sys_getloadavg();
	// Rückgabe der 1, 5 und 15 Minuten Last

	// Lese die CPU-Zeile aus /proc/stat
	$stat1 = explode(" ", preg_replace('!\s+!', ' ', trim(shell_exec("head -n1 /proc/stat"))));
	usleep(100000); // 100ms warten
	$stat2 = explode(" ", preg_replace('!\s+!', ' ', trim(shell_exec("head -n1 /proc/stat"))));

	// user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
	$fields = [1, 2, 3, 4, 5, 6, 7, 8];
	$cpu1 = $cpu2 = 0;
	foreach ($fields as $i) {
		$cpu1 += isset($stat1[$i]) ? (int)$stat1[$i] : 0;
		$cpu2 += isset($stat2[$i]) ? (int)$stat2[$i] : 0;
	}
	$idle1 = isset($stat1[4]) ? (int)$stat1[4] : 0;
	$idle2 = isset($stat2[4]) ? (int)$stat2[4] : 0;

	$totalDiff = $cpu2 - $cpu1;
	$idleDiff = $idle2 - $idle1;

	$cpuPercent = $totalDiff > 0 ? round((1 - ($idleDiff / $totalDiff)) * 100, 1) : 0;

	return [
		'used_percent' => [
			'value' => $cpuPercent,
			'unit' => '%'
		],
		'load_1min' => [
			'value' => $load[0],
			'unit' => ''
		],
		'load_5min' => [
			'value' => $load[1],
			'unit' => ''
		],
		'load_15min' => [
			'value' => $load[2],
			'unit' => ''
		]
	];
}

function getMemoryUsage()
{
	$meminfo = [];
	if (is_readable('/proc/meminfo')) {
		$data = file('/proc/meminfo');
		foreach ($data as $line) {
			list($key, $val) = explode(':', $line);
			$meminfo[trim($key)] = trim($val);
		}
		$total = (int)filter_var($meminfo['MemTotal'], FILTER_SANITIZE_NUMBER_INT);
		$free = (int)filter_var($meminfo['MemAvailable'], FILTER_SANITIZE_NUMBER_INT);
		$used = $total - $free;
		$used_percent = $total > 0 ? round($used / $total * 100, 1) : 0;
		return [
			'used_percent' => [
				'value' => $used_percent,
				'unit' => '%'
			],
			'total' => [
				'value' => round($total / 1024, 2),
				'unit' => 'MB'
			],
			'used' => [
				'value' => round($used / 1024, 2),
				'unit' => 'MB'
			],
			'free' => [
				'value' => round($free / 1024, 2),
				'unit' => 'MB'
			]
		];
	}
	return false;
}

function getPartitionUsage($path, $label)
{
	$diskTotal = @disk_total_space($path);
	$diskFree = @disk_free_space($path);
	if ($diskTotal === false || $diskFree === false) {
		return false;
	}
	$diskUsed = $diskTotal - $diskFree;
	return [
		$label . '_used_percent' => [
			'value' => round($diskUsed / $diskTotal * 100, 1),
			'unit' => '%'
		],
		$label . '_total' => [
			'value' => round($diskTotal / 1024 / 1024 / 1024, 2),
			'unit' => 'GB'
		],
		$label . '_used' => [
			'value' => round($diskUsed / 1024 / 1024 / 1024, 2),
			'unit' => 'GB'
		],
		$label . '_free' => [
			'value' => round($diskFree / 1024 / 1024 / 1024, 2),
			'unit' => 'GB'
		]
	];
}

function getServiceStatus($services)
{
	$result = [];
	foreach ($services as $service) {
		// systemctl is-active gibt "active" oder "inactive" (oder andere) zurück
		$status = trim(shell_exec('systemctl is-active ' . escapeshellarg($service)));
		$result[$service] = $status;
	}
	return $result;
}

function getTopCpuProcesses($limit)
{
	// ps gibt: PID, Benutzer, CPU-Auslastung, Speicher, Befehl
	$cmd = "ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu | head -n " . ($limit + 1);
	$output = [];
	exec($cmd, $output);

	$result = [];
	// Erste Zeile ist die Überschrift
	for ($i = 1; $i < count($output); $i++) {
		// Spalten trennen (mehrere Leerzeichen)
		$cols = preg_split('/\s+/', trim($output[$i]), 5);
		if (count($cols) === 5) {
			$result[$cols[4] . ' (' . $cols[0] . ')'] = [
				'value' => (float)$cols[2],
				'unit' => '%'
			];
		}
	}
	return $result;
}

// API-Handler
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
	header('Content-Type: application/json');
	$input = json_decode(file_get_contents('php://input'), true);

	if (isset($input['action'])) {
		// POST: Dienst neustarten
		switch ($input['action']) {
			case 'restart_service':
				// Aktion zum Neustarten eines Dienstes
				if (
					isset($input['service']) &&
					in_array($input['service'], $serviceList, true)
				) {
					$service = escapeshellarg($input['service']);
					// Neustart des Dienstes (nur wenn root-Rechte vorhanden!)
					$output = [];
					$returnVar = 0;
					exec("sudo systemctl restart $service 2>&1", $output, $returnVar);
					echo json_encode([
						'status' => $returnVar === 0 ? 'ok' : 'error',
						'service' => $input['service'],
						'output' => $output
					]);
					exit;
				} else {
					http_response_code(400);
					echo json_encode(['status' => 'error', 'message' => 'Dienst nicht erlaubt.']);
					exit;
				}
				break;
			default:
				http_response_code(400);
				echo json_encode(['status' => 'error', 'message' => 'Ungültige Aktion.']);
				exit;
		}
	}
} else if ($_SERVER['REQUEST_METHOD'] === 'GET') {
	// GET: Statusabfrage
	if (php_sapi_name() !== 'cli' && basename($_SERVER['SCRIPT_FILENAME']) === 'systeminfo_api.php') {
		header('Content-Type: application/json');
		echo json_encode([
			'hardwareInfo' => getHardwareInfo(),
			'networkInfo' => getNetworkInfo(),
			'softwareInfo' => getSoftwareInfo(),
			'cpuLoad' => getCpuLoad(),
			'memory' => getMemoryUsage(),
			'top10CpuProcesses' => getTopCpuProcesses($numTopProcesses),
			'services' => getServiceStatus($serviceList),
			'storage (root)' => getPartitionUsage('/', 'root'),
			'storage (boot)' => getPartitionUsage('/boot', 'boot'),
			'storage (ramdisk)' => getPartitionUsage('/var/www/html/openWB/ramdisk', 'ramdisk'),
		]);
		exit;
	}
} else {
	http_response_code(405);
	header('Allow: GET, POST');
	echo json_encode(['status' => 'error', 'message' => 'Method not allowed.']);
	exit;
}
