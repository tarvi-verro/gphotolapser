#!/usr/bin/env python
# Based off of http://stackoverflow.com/a/1205762 [2016-03-12]

__all__ = ["monotonic_time"]

from time import sleep
import ctypes, os

CLOCK_MONOTONIC_RAW = 4 # see <linux/time.h>

class timespec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_long),
        ('tv_nsec', ctypes.c_long)
    ]

librt = ctypes.CDLL('librt.so.1', use_errno=True)
clock_gettime = librt.clock_gettime
clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]

def monotonic_time():
    t = timespec()
    if clock_gettime(CLOCK_MONOTONIC_RAW , ctypes.pointer(t)) != 0:
        errno_ = ctypes.get_errno()
        raise OSError(errno_, os.strerror(errno_))
    return t.tv_sec + t.tv_nsec * 1e-9

# Block until specified monotonic time. Plus-minus 1ms unless time has passed.
def monotonic_alarm(wup):
    t = monotonic_time()
    delta = wup - t
    if delta > 0.5: # First get to the half-second range
        sleep(delta - 1.0/10**1)
        t = monotonic_time()
        delta = wup - t
    if delta > 1.0/10**1:
        sleep(delta - 1.0/10**2)
        t = monotonic_time()
        delta = wup - t
    if delta > 1.0/10**2:
        sleep(delta - 1.0/10**3)
        t = monotonic_time()
        delta = wup - t
    if delta > 1.0/10**3:
        sleep(delta)

if __name__ == "__main__":
    print(monotonic_time())

