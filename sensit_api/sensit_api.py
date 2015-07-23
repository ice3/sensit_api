import json
from hashlib import sha1
import os

import datetime
from dateutil.parser import parse
from collections import namedtuple

import requests
from pprint import pprint

base_url = "https://api.sensit.io/v1"

def get_value_if_valid(request, key):
	if request.status_code != 202:
		print("Error")
		print(request)
		print(request.text)
		return None
	else:
		return key(request)

def get_password():
	password = os.getenv("SENSIT_PASS")
	if not password:
		import getpass
		password = getpass.getpass("Sens'it password: ")
	return password

def get_token(mail, password):
	data = json.dumps({
		"password": sha1(password).hexdigest().decode(),
		"email": mail
		})
	r = requests.post(base_url+"/auth", data)
	token = get_value_if_valid(r, lambda r: r.json()["data"]["token"])
	return token

def query_api(url):
	""" Used to encapsulate the header
	"""
	return requests.get(base_url + url, headers=query_api.header)

def parse_sensor_interval(t):
	return map(float, t.split(":"))

class Temperature():
	nb_elem_complete = 1
	nb_elem_specific = 2

	def __init__(self, data):
		self.date = parse(data["date"])
		if "date_period" in data:
			self.interval_begin = parse(data["date_period"])

		values = parse_sensor_interval(data["data"])
		if len(values) == self.nb_elem_specific:
			self.min, self.max = values
			self.value = (self.min + self.max)/2
			self.mode="complete"
		else:
			self.value = values
			self.mode = "specific"
		if isinstance(self.value, list):
			self.value = sum(self.value)*1.0/len(self.value)

class Sound():
	nb_elem_specific = 4
	nb_elem_complete = 3

	def __init__(self, data):
		self.date = parse(data["date"])
		if "date_period" in data:
			self.interval_begin = parse(data["date_period"])

		values = parse_sensor_interval(data["data"])
		if len(values) == self.nb_elem_complete:
			self.value, self.min, self.max = values
			self.mode="complete"

		else:
			self.threshold, self.value, self.min, self.max = values
			self.mode="specific"

class Motion():
	nb_elem_specific = 1
	nb_elem_complete = 2

	def __init__(self, data):
		self.date = parse(data["date"])
		if "date_period" in data:
			self.interval_begin = parse(data["date_period"])

		values = parse_sensor_interval(data["data"])
		if len(values) == self.nb_elem_complete:
			self.threshold, self.value = values
			self.mode="complete"
		else:
			self.value = values
			self.mode="specific"


def convert_sensor_infos(datas, interval, Quantity, complete_mode):
	if not datas:
		return datas

	return [Quantity(d) for d in datas]


class SensitDevice():
	def __init__(self, id_, activation_date, last_comm_date):
		self.id_ = id_
		self.activation_date = parse(activation_date)
		self.last_comm_date = parse(last_comm_date)

	def query_sensors(self):
		def sensors_and_id(request):
			request = request.json()
			sensors = request["data"]["sensors"]
			return {s["sensor_type"]: s["id"] for s in sensors}

		def mode(request):
			return request.json()["data"]["mode"]

		url = "/devices/{}/".format(self.id_)
		request = query_api(url)
		self.current_mode = get_value_if_valid(request, mode)
		self.sensors = get_value_if_valid(request, sensors_and_id)

	def sensor_info(self, kind, last, begin, end):
		def normalize_date(request, target):
			res = None
			if request == -1:
				res = target
			if isinstance(request, str):
				res = parse(request)
			return res

		def check_arguments(last, begin, end):
			if not last and not begin and not end:
				raise TypeError("{}() needs 2 parameters: 0 given.")

			if last and begin and end:
				raise TypeError("{}() needs 2 parameters: 3 given.")

			begin = normalize_date(begin, self.activation_date)
			end = normalize_date(end, self.last_comm_date)

			if begin :
				if self.activation_date > begin:
					raise TypeError("{}(): given 'begin' is before activation date.")
			if end :
				if end > self.last_comm_date:
					raise TypeError("{}(): given 'end' is after current date.")
			if begin and end:
				if begin > end:
					raise TypeError("{}(): given before is after given end.")

			return True

		def parse_links(r):
			links = r.json()["links"]
			return {k:i.split("/api/v1")[1] for k, i in links.items()}

		def get_history(r):
			return r.json()["data"]["history"]

		def get_data(url):
			request = query_api(url)
			datas = get_value_if_valid(request, get_history)
			links = get_value_if_valid(request, parse_links)
			return datas, links

		def check_present(datas, links):
			if not datas :
				return False
			if not links or "next" not in links:
				return False
			return True

		def next_n_data(url, n):
			datas, links = get_data(url)

			if not check_present(datas, links):
				return datas

			while len(datas) < n:
				t_datas, links = get_data(links["next"])
				datas += t_datas
				if not check(datas, links):
					break
			datas = datas[:n]
			return datas

		def data_until(date):
			url = "/devices/{}/sensors/{}".format(self.id_, kind)
			t_datas, links = get_data(url)
			current_date = parse(t_datas[-1]["date"])

			if not check_present(t_datas, links):
				return t_datas

			while current_date > date:
				temp, links = get_data(links["next"])
				t_datas += temp
				current_date = parse(temp[-1]["date"])
				if not check_present(temp, links):
					break

			return t_datas, links
		#######################################################

		if not check_arguments(last, begin, end):
			return None
		begin = normalize_date(begin, self.activation_date)
		end = normalize_date(end, self.last_comm_date)


		if not begin and not end:
			url = "/devices/{}/sensors/{}".format(self.id_, kind)
			datas = next_n_data(url, last)
			return datas

		if begin:
			t_datas, _ = data_until(begin)
			if end:
				datas = filter(lambda x: begin<parse(x["date"])<end, t_datas)
			if last:
				datas = filter(lambda x: begin<parse(x["date"]), t_datas)[-last:]
			return datas

		if end:
			_, links = data_until(end)
			t_datas = next_n_data(links["next"], last)
			return t_datas

	def button(self, last=None, begin=None, end=None):
		try:
			datas = self.sensor_info(self.sensors["button"], last, begin, end)
		except TypeError as e:
			raise TypeError(e.message.format("button"))

		Button = namedtuple("Button", "date")
		return map(parse, [Button(d["date"]) for d in datas])

	def sound(self, last=None, begin=None, end=None, interval=False, complete_mode=True):
		try:
			datas = self.sensor_info(self.sensors["sound"], last, begin, end)
		except TypeError as e:
			raise TypeError(e.message.format("sound"))

		field_complete = "period_start period_end threshold nb_detected min max"
		field_specific = "date nb_detected min max"
		return convert_sensor_infos(datas, interval, Sound, complete_mode)

	def temperature(self, last=None, begin=None, end=None, interval=False, complete_mode=False):
		try:
			datas = self.sensor_info(self.sensors["temperature"], last, begin, end)
		except TypeError as e:
			raise TypeError(e.message.format("temperature"))


		return convert_sensor_infos(datas, interval, Temperature, complete_mode)


	def motion(self, last=None, begin=None, end=None, interval=False, complete_mode=False):
		try:
			datas = self.sensor_info(self.sensors["motion"], last, begin, end)
		except TypeError as e:
			raise TypeError(e.message.format("motion"))

		field_complete = "period_start period_end threshold nb_detected"
		field_specific = "date nb_detected"

		return convert_sensor_infos(datas, interval, Motion, complete_mode)


class Sensit():
	def __init__(self, token=None, mail=None, password=None):
		if not token:
			token = os.getenv("SENSIT_TOKEN")
		if not token:
			if not password:
				password = get_password()
			if mail:
				token = get_token(mail, password)
		if not token:
			raise IdentificationError

		self.token = token
		self.header = {'Authorization': 'Bearer {}'.format(self.token)}
		query_api.header = self.header

		self.query_devices()
		self.query_sensors()

	def query_devices(self):
		def create_device(device):
			id_ = device["id"]
			activation = device["activation_date"]
			last_comm = device["last_comm_date"]
			return SensitDevice(id_, activation, last_comm)

		def create_devices(r):
			return [create_device(dev) for dev in r.json()["data"]]

		r = query_api("/devices")
		self.devices = get_value_if_valid(r, create_devices)

	def query_sensors(self):
		for device in self.devices:
			device.query_sensors()
