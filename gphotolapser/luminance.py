#!/bin/python2
from math import cos, pi

# N -- fnum, aperture
# S -- ISO speed
# t -- shutter speed
def luminance_calculate(N, S, t, K=12.5):
    return N**2 * K / (t * S)

# L -- luminance
def shutter_calculate(L, N, S, K=12.5):
    return N**2 * K / (L * S)

def iso_calculate(L, N, t, K=12.5):
    return N**2 * K / (t * L)

def aperture_calculate(L, S, t, K=12.5):
    return ((L * t * S) / K)**0.5

# Estimate luminance based on sun position
# Sundir is the azimuth relative to camera pointing direction
def luminance_estimate(sunheight, sundir):
    j = 7000. / (1. + 2**(-sunheight + 5.7))
    k = 4. / (2**(1. - cos(sundir*pi/360.)**16)) - 1.
    return j * k + 0.005


def cmp(a,b):
    return (a > b) - (a < b)

# inp must be array of enumerated values.
# Returns two closest candidates.
def get_closest(tgt, inp):
    if len(inp) == 1:
        return (inp[0], inp[0])

    fst=inp[0]
    c=cmp(tgt, inp[0][1])

    for snd in inp[1:]:
        k = cmp(tgt, snd[1])

        if k != c:
            if abs(fst[1] - tgt) > abs(snd[1] - tgt):
                return (snd, fst)
            else:
                return (fst, snd)

        fst = snd

    # tgt doesn't lie between inputs' range
    raise ValueError


# Calculates best fit camera settings for given scene luminance
def luminance_settings_get(target_lumi, aperture_all, iso_all, shutter_all,
        iso_max=800, shutter_min=(1./400.), shutter_max=30, bulb_min=5,
        aperture_min=0.0):

    # Pair up with indecies and sort from fastest to slowest
    av_pairs = sorted(filter(
        lambda p: type(p[1]) is float and p[1] >= aperture_min,
        enumerate(aperture_all)
        ), key = lambda p: p[1], reverse=True)
    iso_pairs = sorted(filter(
        lambda p: type(p[1]) is float and p[1] <= iso_max,
        enumerate(iso_all)
        ), key=lambda p: p[1])
    shutter_pairs = sorted(filter(
        lambda p: type(p[1]) is float and p[1] <= shutter_max and p[1] >= shutter_min,
        enumerate(shutter_all)
        ), key=lambda p: p[1])

    # Get some special values
    iso_auto = filter(
            lambda p: type(p[1]) is str and p[1].lower() == 'auto',
            enumerate(iso_all))
    shutter_bulb = filter(
            lambda p: type(p[1]) is str and p[1].lower() == 'bulb',
            enumerate(shutter_all))

    # Begin with the slowest
    av = av_pairs[-1]
    iso = iso_pairs[-1]
    shutter = shutter_bulb[0]
    bulb = shutter_max

    # First see whether we can lower ISO
    x = iso_calculate(target_lumi, av[1], bulb)
    if x >= iso_max:
        # Scene is too dark, return slowest settings
        return (av[0], iso[0], shutter_bulb[0][0], shutter_max)
    elif x <= iso_max and x >= iso_pairs[0][1]:
        # In ISO range, refine using BULB
        iso = max(get_closest(x, iso_pairs), key=lambda p: p[1])
        bulb = min(shutter_max, shutter_calculate(target_lumi, av[1], iso[1]))
        return (av[0], iso[0], shutter_bulb[0][0], bulb)
    # Use the fastest ISO
    iso = iso_pairs[0]

    # Second see whether limited shutter can put us in of the luminance
    x = shutter_calculate(target_lumi, av[1], iso[1])
    if x >= shutter_min:
        if x >= bulb_min:
            bulb = min(shutter_max, x)
            return (av[0], iso[0], shutter_bulb[0][0], bulb)
        (shutter, _) = get_closest(x, shutter_pairs)
        # But maybe bulb_min is closer
        if abs(x - shutter[1]) > abs(x - bulb_min):
            return (av[0], iso[0], shutter_bulb[0][0], bulb_min)
        return (av[0], iso[0], shutter[0], None)
    # Use the fastest shutter
    shutter = shutter_pairs[0]

    # See how far aperture must be limited
    x = aperture_calculate(target_lumi, iso[1], shutter[1])
    (av, _) = get_closest(x, av_pairs)
    return (av[0], iso[0], shutter[0], None)

