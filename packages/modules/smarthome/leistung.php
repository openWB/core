<?php
$number = $_GET['d'];
$file = "/var/www/html/openWB/ramdisk/device" . $number . "_watt";
if (is_file($file)) {
	$a = file_get_contents($file);
	echo $a;
} else { echo 0; }
?>