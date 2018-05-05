#!/bin/python2
# coding=UTF-8

from __future__ import print_function
import sys
from os import listdir
from os.path import isfile, join, getctime
import time
import pyexiv2
import ctypes
import luminance
from math import log
import numpy as np
from PIL import Image

# Oh look, https://en.wikipedia.org/wiki/Exposure_value#EV_as_a_measure_of_luminance_and_illuminance
# â L = 2^(EV - 3), booyah

def img_histmid(ipath, vcrop=False):
    img_raw = Image.open(ipath)
    [width,height] = img_raw.size
    if vcrop:
        img = img_raw.crop((0, height / 16, width, height / 16 + height / 8 * 7))
    else:
        img = img_raw
    h=img.histogram()
    hsum_thumb = map((lambda x, y, z: x+y+z), h[0:256], h[256:512], h[512:768])
    mx = float(max(hsum_thumb))
    hsum_thumb_corr = map((lambda x: x/mx), hsum_thumb)
    cgx = sum(hsum_thumb * np.arange(0, len(hsum_thumb)))/sum(hsum_thumb)
    return cgx / 256.0


def luminance_from_img(i):
    settings_equivelant=0
    hist_corrected=0
    measured_ev=0
    measured_ev2=0

    md = pyexiv2.ImageMetadata(i)
    md.read()

    N = float(md['Exif.Photo.FNumber'].value);
    S = md['Exif.Photo.ISOSpeedRatings'].value
    t = float(md['Exif.Photo.ExposureTime'].value)
    lumi = luminance.luminance_calculate(N, S, t);
    settings_equivelant = lumi

    # Histogram corrected value
    md.exif_thumbnail.write_to_file('.thmb') # Use thumbnail for max speed
    h = img_histmid('.thmb.jpg', vcrop=True) - 0.5
    hist_corrected = 2**(log(lumi)/log(2) + 20.0*(h**3) + h*3.0)

    # The measured EV values
    ev1_raw = md['Exif.CanonSi.MeasuredEV'].raw_value
    ev2_raw = md['Exif.CanonSi.MeasuredEV2'].raw_value
    measured_ev = 2**((ctypes.c_short(int(ev1_raw)).value/32.0 + 5.0) - 3.0)
    measured_ev2 = 2**((int(ev2_raw)/8.0 - 6.0) - 3.0)

    return (settings_equivelant, hist_corrected, measured_ev, measured_ev2,
            h)

def luminance_calculate(imgd):
    tc=time.time() - 2*60.0
    lst=[]
    lstF=[]

    ls=listdir(imgd)
    ls.sort(reverse=True)

    for i in ls:
        f = join(imgd, i)

        if getctime(f) < tc:
            continue

        if not isfile(f) or i[-3:] != 'JPG' and i[-3:] != 'CR2':
            continue

        try:
            (settings_equivelant, hist_corrected, measured_ev, measured_ev2, histmid) = luminance_from_img(f)
        except IOError:
            print('got ioerror')
            continue


        lst.append(hist_corrected)
        lstF.append(f)

        if len(lst) >= 3:
            break

    if len(lst) == 0:
        return 10000.0

    ev = sum(lst) / len(lst)

    print('Files: {}'.format(lstF))

    #print('Averaging over: {}'.format(len(lst)))

    return float(ev)

#luminance_calculate('/srv/camera')


def main(argc, argv):
    if argc != 2:
        print('Usage: luminance_calculate.py [image]', file=sys.stderr)
        exit(1)

    (settings_equivelant, hist_corrected, measured_ev, measured_ev2, histmid) = luminance_from_img(argv[1])

    print("Measured:            " + str(measured_ev) + ", " + str(measured_ev2))
    print("Settings optimal:    " + str(settings_equivelant))
    print("Histogram corrected: " + str(hist_corrected) + " (" + str(histmid) + ")")

if __name__ == "__main__":
    main(len(sys.argv), sys.argv)

