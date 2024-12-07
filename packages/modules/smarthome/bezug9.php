<?php
$file = "/var/www/html/openWB/ramdisk/device9_wh";
if (is_file($file)) {
	$a = file_get_contents($file);
	echo $a / 1000;
} else { echo 0; }
?>