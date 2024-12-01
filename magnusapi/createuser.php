<?php

require_once "magnusbilling.php";

$api_key = 'xcdtvf4567ctfvg56ftvg56ft';
$api_secret = 'CTFVG567FVTG56FCTVG56FTCVG56ftVG';

$magnusBilling = new MagnusBilling($api_key, $api_secret);
$magnusBilling->public_url = "http://143.244.139.43/mbilling";

$length = 32;
$key = "";
for ($i=1;$i<=$length;$i++) {
  $alph_from = 65;
  $alph_to = 90;

  $num_from = 48;
  $num_to = 57;

  $chr = rand(0,1)?(chr(rand($alph_from,$alph_to))):(chr(rand($num_from,$num_to)));
  if (rand(0,1)) $chr = strtolower($chr);
  $key.=$chr;
  }

function randomPassword() {
    $alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890';
    $pass = array();
    $alphaLength = strlen($alphabet) - 1; //put the length -1 in cache
    for ($i = 0; $i < 8; $i++) {
        $n = rand(0, $alphaLength);
        $pass[] = $alphabet[$n];
    }
    return implode($pass);
}

$userData = [
    'username' => $argv[1],
    'password' => randomPassword(),
    'firstname' => 'false',
    'active' => '1',
    'email' => $key,    
    'id_group' => 3,
    'id_plan' => 1,
    'credit' => $argv[2], 
];

$result = $magnusBilling->createUser($userData);


print_r($result);

?>
