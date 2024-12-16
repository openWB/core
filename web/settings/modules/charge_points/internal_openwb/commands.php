<?php
$valid_commands = array(
  "update_pro_plus"
);
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
  print("invalid request");
  http_response_code(400);
  exit(1);
}
if (!isset($_REQUEST["command"])) {
  print("missing command");
  http_response_code(400);
  exit(1);
}
if (!in_array($_REQUEST["command"], $valid_commands)) {
  print("unsupported command: " . $_REQUEST["command"]);
  http_response_code(400);
  exit(1);
}

print("executing command '" . $_REQUEST["command"] . "'\n");
switch ($_REQUEST["command"]) {
  case 'update_pro_plus':
    $post_data = array("update" => 1);
    $url = "http://192.168.192.50/connect.php";
    $options = array(
      "http" => array(
        "header" =>  "Content-type: application/x-www-form-urlencoded",
        'method'  => 'POST',
        'content' => http_build_query($post_data)
      )
    );
    $context  = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    break;
}

if ($result === false) {
  print("command failed");
  http_response_code(500);
  exit(1);
}

print("command done");
