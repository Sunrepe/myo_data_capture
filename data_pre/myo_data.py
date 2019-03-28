import collections
import myo
import time
import sys
import csv
import os
import numpy as np
from matplotlib import pyplot as plt

# all pose:use it for name output_file
alllei = ['p', 'double', 'fist', 'spread', 'six', 'wavein', 'waveout', 'yes', 'no', 'finger', 'snap']

# Global parameters:
motion_Label = 10
peoplename = 'simengbin'
num_act = 20
windows_len = 80
threshold = 5.0

# files for save myo data
a_filename = '../myodata/oridata/'+peoplename+'_'+alllei[motion_Label]+'_a.txt'
b_filename = '../myodata/actdata/'+peoplename+'_'+alllei[motion_Label]+'_b.txt'
c_filename = '../myodata/actdata/'+peoplename+'_'+alllei[motion_Label]+'_c.txt'

# if recode again
# os.remove(a_filename)
# os.remove(b_filename)
# os.remove(c_filename)

csvfile = open(a_filename, "a", newline='')
writer = csv.writer(csvfile)

# make sure cut right
file_pictest_origin = '../data/picori.txt'
file_pictest_smooth = '../data/picsmo.txt'
os.remove(file_pictest_origin)
os.remove(file_pictest_smooth)
fileori = open(file_pictest_origin, "a", newline='')
filesmo = open(file_pictest_smooth, "a", newline='')
csv_ori = csv.writer(fileori)
csv_smo = csv.writer(filesmo)


def Matrix_to_CSV(filename, data):
    with open(filename, "a", newline='', ) as csvfiles:
        writers = csv.writer(csvfiles)
        for row in data:
            writers.writerow(row)


class EmgDataRecode(myo.DeviceListener):
    def __init__(self, n_Windows, f_forcut):
        super(EmgDataRecode, self).__init__()
        # time/last_time/n for rate recode
        self.__slideWindow = collections.deque(maxlen=n_Windows)
        self.__nfwindows = float(n_Windows)
        self.__fcut = f_forcut
        self.activeEMG = collections.deque()
        self.active_NUM = 0
        self.onrecdoe = False
        self.unrelax = False
        self.tmpslide = 0.0  # just for print check:see the
        self.tmplen = 0  # just for print check

        self.__behind = int(n_Windows/2)
        self.__allwait = False
        self.__tt = None

    @property
    def rate(self):
        if not self.times:
            return 0.0
        else:
            return 1.0 / (sum(self.times) / float(self.n))

    def on_connected(self, event):
        print("Hello, '{}'! Double tap to exit.".format(event.device_name))
        event.device.stream_emg(True)

    def calulate_slideWindows(self):
        p = []
        for _ in self.__slideWindow:
            p.append(sum(list(map(abs, _)))/8.0)
        return sum(p)/self.__nfwindows

    def on_emg(self, event):
        self.__emg = event.emg
        writer.writerow(self.__emg)
        self.__slideWindow.append(self.__emg)
        tmp = sum(list(map(abs, self.__emg)))/8.0

        self.tmpslide = self.calulate_slideWindows()
        self.onrecdoe = True if(self.tmpslide > self.__fcut) else False

        if self.onrecdoe:
            csv_smo.writerow([tmp])
            csv_ori.writerow([tmp])
        else:
            csv_smo.writerow([0.0])
            csv_ori.writerow([tmp])

        # 根据状态进行记录
        # active结束了,但是unrelax还未结束,表示该动作截止.
        if self.__allwait:
            if self.__behind == 1:
                self.__allwait = False
                print()
                print('Valid Act_Length:', len(self.activeEMG))
                print("Valid EMG_Rate:", len(self.activeEMG)/(time.clock()-self.__tt))
                Matrix_to_CSV(b_filename, self.activeEMG)
                Matrix_to_CSV(c_filename, [[len(self.activeEMG)]])
                self.active_NUM += 1
                self.activeEMG.clear()
                self.__behind = int(self.__nfwindows/2.0)
            else:
                self.__behind -= 1
                self.activeEMG.append(self.__emg)
        else:
            if self.onrecdoe:
                if not self.unrelax:
                    self.__tt = time.clock()
                    for _ in range(int(self.__nfwindows/2), int(self.__nfwindows)):
                        self.activeEMG.append(self.__slideWindow[_])
                else:
                    self.activeEMG.append(self.__emg)
            elif self.unrelax:  # 记录结束,写入结果并及时改写unrelax和清空activeEMG
                self.unrelax = False
                print()
                print('Act length:', len(self.activeEMG), end='')
                # sys.stdout.flush()
                if len(self.activeEMG) > 150:
                    self.__allwait = True
                else:
                    self.activeEMG.clear()
                    self.__tt = None
            self.unrelax = True if self.onrecdoe else False


def main():
    myo.init(sdk_path='./myo-sdk-win-0.9.0/')
    hub = myo.Hub()
    listener = EmgDataRecode(n_Windows=windows_len, f_forcut=threshold)
    while hub.run(listener.on_event, 500):
        print('\rAct Num:', listener.active_NUM, '\tSlide mean:', listener.tmpslide, end='')
        sys.stdout.flush()
        if listener.active_NUM >= num_act:
            break
    print("\nYour Pose:", alllei[motion_Label])
    print("\n\033[1;32;mFinish!  Please have a rest!")
    csvfile.close()
    fileori.close()
    filesmo.close()

    # pic for check!
    f1 = plt.figure(5)
    d = np.loadtxt(file_pictest_origin)
    plt.subplot(211)
    plt.plot(d)
    newd = np.loadtxt(file_pictest_smooth)
    plt.subplot(212)
    plt.plot(newd)
    plt.savefig('../myodata/oridata/'+peoplename+'_'+alllei[motion_Label]+'.png', dpi=600, bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    main()
