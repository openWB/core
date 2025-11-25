<?php
$target_dir = $_SERVER["DOCUMENT_ROOT"] . "/openWB/data/";
$target_file = "";
// Optionaler Schlüsseldatei-Pfad für GPG Passphrase
$BACKUP_KEY_FILE = "/home/openwb/backup.key";

function exit_with_error($message)
{
  http_response_code(400);
  echo "Beim Upload der Datei ist ein Fehler aufgetreten!<br />";
  echo $message;
  exit(1);
}

// Prüfen ob Datei GZip testbar ist
function check_gzip($path)
{
  $cmd = "gunzip -t " . escapeshellarg($path) . " 2>&1";
  exec($cmd, $out, $rc);
  if ($rc !== 0) {
    exit_with_error("Die Datei '" . $path . "' ist kein gültiges GZip Archiv!");
  }
}

// Schneller Inhaltscheck für Restore-Archiv
function check_restore_file_contents($path)
{
  $cmd1 = "tar --list --file=" . escapeshellarg($path) . " | egrep -c '^(mosquitto/.+|mosquitto_local/.+|GIT_HASH|GIT_BRANCH|SHA256SUM|backup.log)$'";
  exec($cmd1, $o1, $rc1);
  $count1 = ($rc1 === 0 && isset($o1[0])) ? (int)$o1[0] : 0;
  if ($count1 !== 6) {
    exit_with_error("Prüfung des Archivinhalts fehlgeschlagen! (Basis-Dateien fehlen)");
  }
  $cmd2 = "tar --list --file=" . escapeshellarg($path) . " | grep -c '^openWB/'";
  exec($cmd2, $o2, $rc2);
  $count2 = ($rc2 === 0 && isset($o2[0])) ? (int)$o2[0] : 0;
  if ($count2 <= 4) {
    exit_with_error("Prüfung des Archivinhalts fehlgeschlagen! (openWB Inhalt zu klein)");
  }
}

// Erkennen ob Datei ein (binär oder ASCII) GPG verschlüsseltes Archiv ist
function is_gpg_file($path)
{
  $out = @shell_exec("file -b " . escapeshellarg($path));
  if ($out === null) return false;
  return (stripos($out, 'GPG') !== false);
}

// Ermittelt die GPG Passphrase:
function get_gpg_passphrase($keyFile)
{
  // erst aus POST, sonst aus Schlüsseldatei
  if (isset($_POST["restorePassword"]) && is_string($_POST["restorePassword"]) && $_POST["restorePassword"] !== '') {
    return $_POST["restorePassword"];
  }
  if (is_readable($keyFile)) {
    $raw = file_get_contents($keyFile);
    if ($raw === false) {
      exit_with_error("Konnte Schlüsseldatei nicht lesen.");
    }
    // Nur erste Zeile / trim
    $line = trim(preg_split("/\r\n|\n|\r/", $raw, 2)[0]);
    if ($line === '') {
      exit_with_error("Schlüsseldatei ist leer.");
    }
    return $line;
  }
  exit_with_error("Passphrase für GPG fehlt (weder Eingabe noch Schlüsseldatei vorhanden).");
}

// GPG symmetrisch entschlüsseln (Passphrase via STDIN, kein Leak in Prozessliste)
function decrypt_gpg($srcPath, $passphrase)
{
  $dest = tempnam(sys_get_temp_dir(), 'openwb_dec_');

  // create a writable temporary gpg home for this operation
  $gpg_home = sys_get_temp_dir() . '/openwb_gnupg_' . uniqid();
  if (!mkdir($gpg_home, 0700, true) && !is_dir($gpg_home)) {
    @unlink($dest);
    exit_with_error("Konnte temporäres GPG-Homedir nicht anlegen.");
  }
  chmod($gpg_home, 0700);

  $cmd = "gpg --homedir " . escapeshellarg($gpg_home)
    . " --batch --yes --pinentry-mode=loopback --passphrase-fd 0 -o "
    . escapeshellarg($dest) . " -d " . escapeshellarg($srcPath);

  $descriptors = [
    0 => ["pipe", "r"],
    1 => ["pipe", "w"],
    2 => ["pipe", "w"],
  ];
  $proc = proc_open($cmd, $descriptors, $pipes);
  if (!is_resource($proc)) {
    @unlink($dest);
    @exec('rm -rf ' . escapeshellarg($gpg_home));
    exit_with_error("GPG konnte nicht gestartet werden.");
  }

  fwrite($pipes[0], $passphrase . PHP_EOL);
  fclose($pipes[0]);
  $stdout = stream_get_contents($pipes[1]);
  fclose($pipes[1]);
  $stderr = stream_get_contents($pipes[2]);
  fclose($pipes[2]);
  $rc = proc_close($proc);

  // cleanup temporary gpg home
  @exec('rm -rf ' . escapeshellarg($gpg_home));

  if ($rc !== 0) {
    @unlink($dest);
    exit_with_error("GPG Entschlüsselung fehlgeschlagen: " . htmlspecialchars($stderr));
  }
  return $dest;
}

if (!isset($_FILES["file"]) || !is_uploaded_file($_FILES["file"]["tmp_name"])) {
  exit_with_error("Keine Datei hochgeladen.");
}

$uploaded_tmp = $_FILES["file"]["tmp_name"];
$work_file = $uploaded_tmp;  // Datei gegen die die Prüfungen laufen
$decrypted_temp = null;
$is_gpg = false;

if (isset($_POST["target"])) {
  switch ($_POST["target"]) {
    case 'restore':
      $target_file = $target_dir . "restore/" . "restore.tar.gz";
      // Erkennen ob GPG
      if (is_gpg_file($uploaded_tmp)) {
        $is_gpg = true;
        $passphrase = get_gpg_passphrase($BACKUP_KEY_FILE);
        $decrypted_temp = decrypt_gpg($uploaded_tmp, $passphrase);
        $work_file = $decrypted_temp;
      }
      check_gzip($work_file);
      check_restore_file_contents($work_file);
      break;
    case 'migrate':
      $target_file = $target_dir . "data_migration/" . "data_migration.tar.gz";
      check_gzip($work_file);
      break;
    default:
      exit_with_error("Fehlender oder ungültiger Parameter!");
  }
} else {
  exit_with_error("Ziel-Parameter fehlt!");
}

// Datei verschieben: bei GPG den entschlüsselten Inhalt persistieren, sonst das Original
if ($is_gpg) {
  // Validierung: entschlüsselte Datei muss existieren
  if (!$decrypted_temp || !is_file($decrypted_temp)) {
    if ($decrypted_temp && file_exists($decrypted_temp)) @unlink($decrypted_temp);
    exit_with_error("Interner Fehler: Entschlüsselte Datei fehlt.");
  }
  // Versuche rename (schnell), bei Cross-FS fallback auf copy
  if (!@rename($decrypted_temp, $target_file)) {
    if (!@copy($decrypted_temp, $target_file)) {
      @unlink($decrypted_temp);
      exit_with_error("Konnte entschlüsselte Datei nicht verschieben.");
    }
    @unlink($decrypted_temp);
  }
  // Aufräumen: hochgeladenes (verschlüsseltes) Original entfernen
  @unlink($uploaded_tmp);
  echo "Die Datei " . htmlspecialchars(basename($_FILES["file"]["name"])) . " wurde hochgeladen und entschlüsselt (GPG erkannt).";
} else {
  // Unverschlüsselt: normales move_uploaded_file
  if (move_uploaded_file($uploaded_tmp, $target_file)) {
    echo "Die Datei " . htmlspecialchars(basename($_FILES["file"]["name"])) . " wurde hochgeladen.";
  } else {
    if ($decrypted_temp && file_exists($decrypted_temp)) @unlink($decrypted_temp);
    exit_with_error("Beim Verarbeiten der Datei ist ein Fehler aufgetreten!");
  }
}
// Entschlüsseltes Temp-File sollte bereits verschoben/gelöscht sein; Sicherheits-Cleanup:
if ($decrypted_temp && file_exists($decrypted_temp)) {
  @unlink($decrypted_temp);
}
