import botlib


def test_clean_redirect_url():
    module = botlib.get_bot_module('vilnius/vtaryba')
    value = '0;URL=https://edarbuotojas.vilnius.lt/subsystems/dhs/preview/2014/11/24/6537/index.php'
    result = module.clean_redirect_url(value)
    assert result == 'https://edarbuotojas.vilnius.lt/subsystems/dhs/preview/2014/11/24/6537/index.php'
