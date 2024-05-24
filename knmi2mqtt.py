#!/bin/python

import requests, datetime, netCDF4, paho.mqtt.publish

# 6215: Voorschoten
# 6344: Rotterdam The Hague Airport
# 6330: Hoek van Holland
weather_stations = [6330, 6344, 6215]
# anonymous key, valid until 1 July 2024 (possibly unoficially longer?)
# get a new one at https://developer.dataplatform.knmi.nl/open-data-api#token
api_key = "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJpZCI6ImE1OGI5NGZmMDY5NDRhZDNhZjFkMDBmNDBmNTQyNjBkIiwiaCI6Im11cm11cjEyOCJ9"
api_base_url = "https://api.dataplatform.knmi.nl/open-data/v1/datasets"

fields = [
  ('temperature-2m', 'ta', '°C'),
  ('temperature-10cm', 'tgn', '°C'),
  ('humidity', 'rh', '%'),
]

dtNow = datetime.datetime.now(datetime.UTC)
dtSearch = dtNow - datetime.timedelta(minutes = 20 + dtNow.minute % 10)

session = requests.Session()
session.headers.update({'Authorization': api_key})

print("Finding the right file...")

files = session.get(f"{api_base_url}/Actuele10mindataKNMIstations/versions/2/files", params = {
  'startAfterFilename': f"KMDS__OPER_P___10M_OBS_L2_{dtSearch:%Y%m%d%H%M}.nc"
})

fileName = files.json()['files'][-1]['filename']
fileMetadata = session.get(f"{api_base_url}/Actuele10mindataKNMIstations/versions/2/files/{fileName}/url")

rlRemaining = fileMetadata.headers['X-Ratelimit-Remaining']
rlLimit = fileMetadata.headers['X-Ratelimit-Limit']
rlReset = datetime.datetime.fromtimestamp(int(fileMetadata.headers['X-Ratelimit-Reset']))

print(f"Ratelimit stats: {rlRemaining}/{rlLimit} remaining (resets at {rlReset})")

print(f"Found {fileName}, last modified at {files.json()['files'][-1]['lastModified']}, starting download...")

theFile = requests.get(fileMetadata.json()['temporaryDownloadUrl'])

print(f"Downloading completed ({len(theFile.content)/1024:.0f} kb)")

dataset = netCDF4.Dataset(fileName, memory=theFile.content)

assert dataset.variables['time'].units == 'seconds since 1950-01-01 00:00:00', f"{dataset.variables['time']=:}"

# so, we're dealing with a 1950-01-01 epoch. Let's convert it to a unix timestamp
# there are 5 leap years between those epochs: '52, '56, '60, '64, and '68
dt = datetime.datetime.fromtimestamp(dataset.variables['time'][:][0] - (20*365 + 5) * 24*60*60, datetime.UTC)

msgs = []

for station in weather_stations:
  try:
    idx = list(dataset.variables['station']).index(f"{station:05d}")
    print(f"Valid for {dt} (UTC) at station {dataset.variables['stationname'][idx].title()}")

    stationname = dataset.variables['stationname'][idx].lower().replace(' aws', '').replace(' ap', ' airport').title()

    print(f"revspace/sensors/knmi/{station}/stationname = {stationname}")
    msgs.append((f"revspace/sensors/knmi/{station}/stationname", stationname, 0, True))
    print(f"revspace/sensors/knmi/{station}/measured-at = {dt.isoformat()}")
    msgs.append((f"revspace/sensors/knmi/{station}/measured-at", dt.isoformat(), 0, True))
    for field in fields:
      print(f"revspace/sensors/knmi/{station}/{field[0]} = {dataset.variables[field[1]][idx][0]} {field[2]}")
      msgs.append((f"revspace/sensors/knmi/{station}/{field[0]}", f"{dataset.variables[field[1]][idx][0]} {field[2]}", 0, True))

  except ValueError:
    print(f"Can't find weather station {station}, skipping...")

paho.mqtt.publish.multiple(msgs, hostname="mosquitto.space.revspace.nl", client_id="knmi2mqtt")
