<?php
$file = "/var/www/html/openWB/ramdisk/device5_watt";
if (is_file($file)) {
	$a = file_get_contents($file);
	echo $a;
} else { echo 0; }
?>