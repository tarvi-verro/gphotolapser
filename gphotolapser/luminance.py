#!/bin/python2
from math import cos, pi

# N -- fnum, aperture
# S -- ISO speed
# t -- shutter speed
def luminance_calculate(N, S, t, K=12.5):
    return N**2 * K / (t * S)

# Estimate luminance based on sun position
# Sundir is the azimuth relative to camera pointing direction
def luminance_estimate(sunheight, sundir):
    j = 7000. / (1. + 2**(-sunheight + 5.7))
    k = 4. / (2**(1. - cos(sundir*pi/360.)**16)) - 1.
    return j * k + 0.005

def luminance_settings_get_bulb(target_lumi, given_aperture, given_iso,
        shutter_min=(1./400.), shutter_max=30):
    t_max = shutter_max
    t_min = shutter_min

    offs=[]

    # Binary search for optimum
    for i in range(0, 60):
        chunk=(t_max-t_min)/2.0
        mid=t_min + chunk
        a = mid - chunk/2.0
        b = mid + chunk/2.0
        a_off = abs(target_lumi - luminance_calculate(given_aperture, given_iso, a))
        b_off = abs(target_lumi - luminance_calculate(given_aperture, given_iso, b))
        if a_off < b_off:
            t_max = mid
            offs+=[a_off]
        else:
            t_min = mid
            offs+=[b_off]

        if offs[-1] < 1.0/4000.0:
            break

    #print(offs)
    return (t_max+t_min)/2.0

# Calculates best fit camera settings for given scene luminance
def luminance_settings_get(target_lumi, aperture, iso, shutter, iso_max=800,
        shutter_min=(1./400.), shutter_max=30):
    # First get the brightest settings
    t_aperture_brig=None
    t_aperture_dark=None
    t_iso_brig=None
    t_iso_dark=None
    t_shutter_brig=None
    t_shutter_dark=None

    # Ordered from brightest to darkest
    for indx, e in enumerate(aperture):
        if type(e) is not float:
            continue
        t_aperture_brig = (indx, e)
        break
    for indx, e in enumerate(aperture):
        if type(e) is not float:
            continue
        t_aperture_dark = (indx, e)

    # Ordered from darkest to brightest
    for indx, e in enumerate(iso):
        if type(e) is not float:
            continue
        if e > iso_max: # Max ISO
            continue
        t_iso_brig = (indx, e)
    for indx, e in enumerate(iso):
        if type(e) is not float:
            continue
        t_iso_dark = (indx, e)
        break

    # Ordered from brightest to darkest
    for indx, e in enumerate(shutter):
        if type(e) is not float:
            continue
        if e > shutter_max:
            continue
        t_shutter_brig = (indx, e)
        break
    for indx, e in enumerate(shutter):
        if type(e) is not float:
            continue
        if e < shutter_min:
            continue
        t_shutter_dark = (indx, e)

    # To begin, we want to lower ISO.
    if target_lumi < luminance_calculate(t_aperture_brig[1], t_iso_dark[1],
            t_shutter_brig[1]):
        first=None
        a = t_aperture_brig
        s = t_shutter_brig
        # Find the best fit for ISO
        for indx, e in enumerate(iso):
            if type(e) is not float:
                continue
            if first == None:
                first = indx
            if e > iso_max:
                break
            # ISO list starts from darkest
            l = luminance_calculate(a[1], e, s[1])
            if target_lumi < l:
                continue
            # Perfect ISO is between [indx; indx-1]
            if indx == first:
                return (a[0], indx, s[0])
            if luminance_calculate(a[1], iso[indx-1], s[1]) - target_lumi < target_lumi - l:
                return (a[0], indx-1, s[0])
            else:
                return (a[0], indx, s[0])
        return (a[0], t_iso_brig[0], s[0])
    # Secondly we'd like to lower exposure times
    elif target_lumi < luminance_calculate(t_aperture_brig[1],
            t_iso_dark[1], t_shutter_dark[1]):
        # Find the best fit for shutter
        first=None
        i = t_iso_dark
        a = t_aperture_brig
        for indx, e in enumerate(shutter):
            if type(e) is not float:
                continue
            if first == None:
                first = indx
            # Shutter values start from brightest
            if shutter_max < e or shutter_min > e:
                continue
            l = luminance_calculate(a[1], i[1], e)
            if target_lumi > l:
                continue
            # Perfect exposure time between [indx; indx-1]
            if indx == first:
                return (a[0], i[0], indx)
            if target_lumi - luminance_calculate(a[1], i[1], shutter[indx-1]) < l - target_lumi:
                return (a[0], i[0], indx-1)
            else:
                return (a[0], i[0], indx)
        return (a[0], i[0], t_shutter_brig[0])
    # Lastly we'll start closing the aperture
    else:
        # Find the best fit aperture setting
        first=None
        i = t_iso_dark
        s = t_shutter_dark
        for indx, e in enumerate(aperture):
            if type(e) is not float:
                continue
            if first == None:
                first = indx
            # Aperture values start from brightest
            l = luminance_calculate(e, i[1], s[1])
            if target_lumi > l:
                continue
            if indx==first:
                return (indx, i[0], s[0])
            if target_lumi - luminance_calculate(aperture[indx-1], i[1], s[1]) < l - target_lumi:
                return (indx-1, i[0], s[0])
            else:
                return (indx, i[0], s[0])
        return (t_aperture_dark[0], i[0], s[0])

    return (t_aperture_brig[0],t_iso_brig[0],t_shutter_brig[0])

