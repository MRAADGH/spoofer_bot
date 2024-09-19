<?php
require_once "magnusbilling.php";

$api_key = 'xcdtvf4567ctfvg56ftvg56ft';
$api_secret = 'CTFVG567FVTG56FCTVG56FTCVG56ftVG';

$magnusBilling = new MagnusBilling($api_key, $api_secret);
$magnusBilling->public_url = "http://193.160.130.149/mbilling";

$id_user = $magnusBilling->getId('user', 'username', $argv[1]);

$today = date('Y-m-d');
$date = date('Y-m-d', strtotime('+1 month', strtotime($today)));

$result = $magnusBilling->update('user',$id_user, [
      'firstname' => 'true',
      'enableexpire' => 1,
      'expirationdate' => $date	
    ]);

print_r($result);