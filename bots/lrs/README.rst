Incapsula apsauga
=================

Norint apeiti Incapsula apsaugą, reikia naršyklėje suvesti paveiksliuke rodomą
apsaugos kodą ir nusikopijuoti ``incap_ses_*`` sausainiukus.

Leidžians skriptą serveryje, naržyklę reikia leisti per serverio proxy.
Serverio SOCS proxy galima įjungti taip::

    ssh -D 8080 remote-server

SOCKS proxy nustatymai naršyklėje: ``127.0.0.1:8080``

Before running this bot run::

    export INCAP_SES=""
