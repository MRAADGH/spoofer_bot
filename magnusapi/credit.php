<?php
require_once "magnusbilling.php";

$api_key = 'xcdtvf4567ctfvg56ftvg56ft';
$api_secret = 'CTFVG567FVTG56FCTVG56FTCVG56ftVG';

$magnusBilling = new MagnusBilling($api_key, $api_secret);
$magnusBilling->public_url = "http://143.244.139.43/mbilling";

$id_user = $magnusBilling->getId('user', 'username', $argv[1]);

$result = $magnusBilling->create('refill', [
    'credit'      => $argv[2],
    'id_user'     => $id_user,
    'payment'     => 1,
    'description' => 'Insert credit from API',

]);

print_r($result);
