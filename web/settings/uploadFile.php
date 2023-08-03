<?php
$target_dir = $_SERVER["DOCUMENT_ROOT"] . "/openWB/data/";
$target_file = "";

function exit_with_error($message){
	http_response_code(400);
	echo "Beim Upload der Datei ist ein Fehler aufgetreten!<br />";
	echo $message;
	exit(1);
}

// check for valid gzip file
function check_gzip() {
	$output = null;
	$result = exec("gunzip -t \"" . $_FILES["file"]["tmp_name"] . "\"", $output);
	if ($result === false) {
		exit_with_error("Die Datei ist kein gültiges GZip Archiv!");
	}
}

// quick check for file contents
function check_restore_file_contents() {
	$output = null;
	$result = exec("tar --list --file=\"" . $_FILES["file"]["tmp_name"] . "\" | grep -c \"^\(openWB/\|mosquitto/\|mosquitto_local/\|GIT_HASH\|GIT_BRANCH\|SHA256SUM\|backup.log\)$\"", $output);
	if ($result === false || $result != "7") {
		exit_with_error("Prüfung des Archivinhalts fehlgeschlagen!");
	}
}

if (isset($_POST["target"])) {
	switch ($_POST["target"]) {
		case 'restore':
			$target_file = $target_dir . "restore/" . "restore.tar.gz";
			check_gzip();
			check_restore_file_contents();
			break;
		case 'migrate':
			$target_file = $target_dir . "data_migration/" . "data_migration.tar.gz";
			check_gzip();
			break;
		default:
			exit_with_error("Fehlende oder ungültiger Parameter!");
	}
}

// if everything is ok, try to accept and move file
if (move_uploaded_file($_FILES["file"]["tmp_name"], $target_file)) {
	echo "Die Datei ". htmlspecialchars( basename( $_FILES["file"]["name"])). " wurde hochgeladen.";
} else {
	exit_with_error("Beim Hochladen der Datei ist ein Fehler aufgetreten!");
}
?>
