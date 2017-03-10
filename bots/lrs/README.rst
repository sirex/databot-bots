Incapsula apsauga
=================

Norint apeiti Incapsula apsaugą, reikia naršyklėje suvesti paveiksliuke rodomą
apsaugos kodą ir nusikopijuoti ``incap_ses_*`` sausainiukus.

Leidžians skriptą serveryje, naržyklę reikia leisti per serverio proxy.
Serverio SOCS proxy galima įjungti taip::

    ssh -D 8080 remote-server

SOCKS proxy nustatymai naršyklėje: ``127.0.0.1:8080``

Prieš leidžiant bouts reikia sukurti ``settings.yml`` failą, jei tokio dar nėra
ir įrašyto tokius nustatymus::

    cookies:
      www3.lrs.lt:
        visid_incap_791905: ARedswaWQGCmn94pTD/xMwr6Q1cAAAAAQkIPAAAAAACA/hJ6AVh3Vx6Bzk5JXwcRZS+eWwmh1saP
        incap_ses_108_791905:
        incap_ses_473_791905:
