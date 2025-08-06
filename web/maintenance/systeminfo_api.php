<?php
// systeminfo_api.php
// This script provides system information in JSON format for API access.
// It is intended to be accessed via AJAX or similar methods.

if (php_sapi_name() !== 'cli' && basename($_SERVER['SCRIPT_FILENAME']) === 'systeminfo_api.php') {
	header('Content-Type: application/json');
	echo json_encode([
		'cpuLoad' => getCpuLoad(),
		'memory' => getMemoryUsage(),
		'storage' => getStorageUsage(),
		'services' => getServiceStatus([
			'openwb2.service',
			'openwbRemoteSupport.service',
			'mosquitto.service',
			'mosquitto_local.service'
		])
	]);
	exit;
}

function getCpuLoad()
{
	$load = sys_getloadavg();
	$cpuCores = (int)@shell_exec('nproc') ?: 1; // Fallback auf 1 Kern, falls nproc nicht verfügbar

	return [
		// '1min' => [
		//     'value' => $load[0],
		//     'unit' => ''
		// ],
		'1min_percent' => [
			'value' => round(($load[0] / $cpuCores) * 100, 1),
			'unit' => '%'
		],
		// '5min' => [
		//     'value' => $load[1],
		//     'unit' => ''
		// ],
		'5min_percent' => [
			'value' => round(($load[1] / $cpuCores) * 100, 1),
			'unit' => '%'
		],
		// '15min' => [
		//     'value' => $load[2],
		//     'unit' => ''
		// ],
		'15min_percent' => [
			'value' => round(($load[2] / $cpuCores) * 100, 1),
			'unit' => '%'
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

function getStorageUsage()
{
	$diskTotal = @disk_total_space("/");
	$diskFree = @disk_free_space("/");
	if ($diskTotal === false || $diskFree === false) {
		return false;
	}
	$diskUsed = $diskTotal - $diskFree;
	return [
		'used_percent' => [
			'value' => round($diskUsed / $diskTotal * 100, 1),
			'unit' => '%'
		],
		'total' => [
			'value' => round($diskTotal / 1024 / 1024 / 1024, 2),
			'unit' => 'GB'
		],
		'used' => [
			'value' => round($diskUsed / 1024 / 1024 / 1024, 2),
			'unit' => 'GB'
		],
		'free' => [
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
