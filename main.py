# -*-coding:utf8 -*-

from matplotlib import pyplot as plt

from sensit_api import Sensit

def transpose(mat):
	return zip(*mat)

if __name__ == "__main__" :
	sens = Sensit()
	dev = sens.devices[0]

	# f, (ax1, ax2) = plt.subplots(2, sharex=True)
	plt.title("Sensit data")

	temps = [(m.date, m.value) for m in dev.sound(begin="2015-07-01T00:00Z", end=-1)]
	dates, values = transpose(temps)
	plt.scatter(dates, values, label="sound")
	plt.legend(loc="best")

	# sounds = [(m.date, m.value) for m in dev.sound(begin=-1, end=-1)]
	# dates, values = transpose(sounds)
	# ax2.plot(dates, values, label="sound")

	# motions = [(m.date, m.value) for m in dev.motion(begin=-1, end=-1)]
	# dates, values = transpose(motions)
	# ax2.plot(dates, values, label="motion")
	# ax2.legend(loc="best")

	plt.show()