<?php

require_once "magnusbilling.php";

$api_key = 'xcdtvf4567ctfvg56ftvg56ft';
$api_secret = 'CTFVG567FVTG56FCTVG56FTCVG56ftVG';

$magnusBilling = new MagnusBilling($api_key, $api_secret);
$magnusBilling->public_url = "http://193.160.130.149/mbilling";

$result = $magnusBilling->read('sip');

$page = 1;

do {
    $result = $magnusBilling->read('sip', $page);

    if (!empty($result) && strpos(print_r($result, true), "[cid_number] =>") !== false) {
        print_r($result);
        $page++;
    } else {
        break;
    }
} while (true);

?>