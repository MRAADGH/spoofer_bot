<?php

require_once "magnusbilling.php";

$api_key = 'xcdtvf4567ctfvg56ftvg56ft';
$api_secret = 'CTFVG567FVTG56FCTVG56FTCVG56ftVG';

$magnusBilling = new MagnusBilling($api_key, $api_secret);
$magnusBilling->public_url = "http://143.244.139.43/mbilling";

$id_user = $magnusBilling->getId('user', 'username', $argv[1]);

$magnusBilling->setFilter('id_user', $id_user, 'eq', 'numeric');

$result = $magnusBilling->read('call');

print_r($result);

