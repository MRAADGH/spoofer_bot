<?php

require_once "magnusbilling.php";

$api_key = 'xcdtvf4567ctfvg56ftvg56ft';
$api_secret = 'CTFVG567FVTG56FCTVG56FTCVG56ftVG';

$magnusBilling = new MagnusBilling($api_key, $api_secret);
$magnusBilling->public_url = "http://143.244.139.43/mbilling";

$id_user = $magnusBilling->getId('user', 'username', $argv[1]);

$id_sip = $magnusBilling->getId('sip', 'id_user', $id_user);

$result = $magnusBilling->update('sip', $id_sip, [
    'callerid'   => $argv[2],
    'cid_number' => $argv[2],

]);

print_r($result);
