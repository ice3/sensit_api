# Sensit API v1

A python library to easily get data from your Sensit device

## What is Sensit?

A [Sensit](https://www.sensit.io/) device is an IoT device created by [Axible](http://www.axible-connects-for-you.com/) with 4 sensor, sending it's data throught the [Sigfox](http://www.sigfox.com/en/) network (a kind of long range wireless network). The data are then pushed to the cloud and are exposed on the sensit.io website which also provides an API to get the data.

The sensors are :
 * temperature
 * noise
 * motion
 * a button

## The API

For complete API doc, go to the [sensit.io website](https://api.sensit.io/v1/)

### Authentification

2 ways to get the auth :
 * via token (created from the website when you query developper access)
 * via mail / password (wich ask for a token, so you should have a developper acces. Only the sha1 hashed version of the sensor is send to the server)

Note that these elements can be given in the code or in shell variables :
 * SENSIT_PASS
 * SENSIT_TOKEN

### Dependency

The only non stdlib dependency is the worderfull `requests` to perform easy HTTP requests
To install :
	pip install request

### Doc

The implementation aims to ease of use and simplicity, so everything is quite straightforward.

First import a Sensit device : `from sensit_api import Sensit`.

Then get your device to query the data :

``` python
sens = Sensit()
dev = sens.devices[0]
data = dev.sound(begin="2015-07-01T00:00Z", end=-1)
data_parsed = [(d.date, d.value) for d in data]
```

The sensors are availlable with the functions:
 * `SensitDevice.sound`
 * `SensitDevice.motion`
 * `SensitDevice.temperature`
 * `SensitDevice.button`

The functions take 2 arguments out of the 3 possibles:
 * `begin`: when we want the data to start
 * `end`: the we want the data to end
 * `last`: we want N data points after begin or before end
 * for the current date (`end`) or the device activation (`begin`), the shortcut value is `-1`

The API to manipulate the data is quite complex because the data change if we are in "complete" (all the sensors values are sent) or "specific" mode. Data fields also change according the sensor kind. For each classic sensors (temperature, sound, motion) `date` and `value` will always be present, for the button, anly the `date` is present because it is the only interesting field.

Here are the possible fileds for each sensor according the mode:
* temperature :
  * specific mode :
    * min, max : the min and max values measured in the time interval
    * value : mean from mean and max
    * mode : "specific"
  * complete :
    * value : mean of the measured temperature in the interval
    * mode : "complete"
    * date_period : beginning of the period during which the data has been measured
* motion :
  * specific mode :
    * threshold : the sensibility of the sensor (between 1 and 4)
    * value : number of motions detected
    * date_period : beginning of the period during which the data has been measured
    * mode : "specific"
  * complete mode :
    * value : number of motions detected
    * mode : "complete"
* sound :
  * specific mode :
    * threshold : the sensibility of the sensor (between 1 and 4)
    * value : number of noises  detected
    * date_period : beginning of the period during which the data has been measured
    * min, max : the min and max values measured in the time interval
    * mode : "specific"
  * complete mode :
    * value : number of noises detected
    * date_period : beginning of the period during which the data has been measured
    * mode : "complete"
* button :
 * date : the datetime when the button was pressed


A complete exemple is presented in the `main.py` file


## TODO :
 * add tests, tests, tests
 * to go faster, compute the first and last page to grab
 * get the pages with `async` (is request still working?)
 * Python 3.4 port
 * easier API for the sensors?