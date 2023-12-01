knmi2mqtt
=========

Should be run 7 minutes after every 10th minute.

* Fancy Cron: `7/10 * * * *`
* Lame Cron: `7,17,27,37,47,57 * * * *`
* Systemd: `OnCalendar=*:7/10`

API key comes from https://developer.dataplatform.knmi.nl/open-data-api#token (does not require an account).
