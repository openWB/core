<?php
$number = $_GET['d'];
$file = "/var/www/html/openWB/ramdisk/device" . $number . "_wh";
if (is_file($file)) {
	$a = file_get_contents($file);
	echo $a / 1000;
} else { echo 0; }
?>