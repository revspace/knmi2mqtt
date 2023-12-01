knmi2mqtt
=========

Should be run 7 minutes after every 10th minute.

* Cron: `7/10 * * * *`
* Systemd: `OnCalendar=*:7/10`

API key comes from https://developer.dataplatform.knmi.nl/open-data-api#token (does not require an account).
