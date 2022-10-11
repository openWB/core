<?php
$target_dir = $_SERVER["DOCUMENT_ROOT"] . "/openWB/data/restore/";
$target_file = $target_dir . "restore.tar.gz";
$upload_ok = true;

// check for valid gzip file
$output = null;
$result = exec("gunzip -t \"" . $_FILES["backupFile"]["tmp_name"] . "\"", $output);
if ($result === false) {
	$upload_ok = false;
	echo "Die Datei ist kein gültiges GZip Archiv!<br />";
}

// quick check for file contents
$output = null;
$result = exec("tar --list --file=\"" . $_FILES["backupFile"]["tmp_name"] . "\" | grep -c \"^\(openWB/\|mosquitto/\|mosquitto_local/\|GIT_HASH\|GIT_BRANCH\|SHA256SUM\|backup.log\)$\"", $output);
if ($result === false || $result != "7") {
	$upload_ok = false;
	echo "Prüfung des Archivinhalts fehlgeschlagen!<br />";
}

// Check if $uploadOk is set to 0 by an error
if (! $upload_ok) {
	http_response_code(400);
	echo "Beim Upload der Datei ist ein Fehler aufgetreten!";
} else {
	// if everything is ok, try to upload file
	if (move_uploaded_file($_FILES["backupFile"]["tmp_name"], $target_file)) {
		echo "Die Datei ". htmlspecialchars( basename( $_FILES["backupFile"]["name"])). " wurde hochgeladen.";
	} else {
		echo "Beim Hochladen der Datei ist ein Fehler aufgetreten!";
	}
}
?>
