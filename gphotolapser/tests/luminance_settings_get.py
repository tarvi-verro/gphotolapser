# To run the test:
#   python2 -m gphotolapser.tests.luminance_settings_get

from ..luminance import luminance_settings_get, luminance_calculate

# Canon 550D values
class Canon_550D:
    aperture = [3.5, 4.0, 4.5, 5.0, 5.6, 6.3, 7.1, 8.0, 9.0, 10.0, 11.0, 13.0,
            14.0, 16.0, 18.0, 20.0, 22.0]
    shutter = ['bulb', 30.0, 25.0, 20.0, 15.0, 13.0, 10.0, 8.0, 6.0, 5.0, 4.0,
            3.2, 2.5, 2.0, 1.6, 1.3, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2,
            0.16666666666666666, 0.125, 0.1, 0.07692307692307693,
            0.06666666666666667, 0.05, 0.04, 0.03333333333333333, 0.025, 0.02,
            0.016666666666666666, 0.0125, 0.01, 0.008, 0.00625, 0.005, 0.004,
            0.003125, 0.0025, 0.002, 0.0015625, 0.00125, 0.001, 0.0008,
            0.000625, 0.0005, 0.0004, 0.0003125, 0.00025]
    iso = ['Auto', 100.0, 200.0, 400.0, 800.0, 1600.0, 3200.0, 6400.0, 12800.0]


# Check whether output values equivelant luminance grows monotonically
def check_monotonical_growth(sets, r):
    success = True
    for i in range(1, len(r)-1):
        # Values for previous step
        (p_av_i, p_iso_i, p_shutter_i, p_bulb) = luminance_settings_get(r[i-1],
                sets.aperture, sets.iso, sets.shutter,
                iso_max=1600, bulb_min=3, shutter_min=(1/1000.))
        p_shutter = p_bulb
        if p_bulb == None:
            p_shutter = sets.shutter[p_shutter_i]
        p_lumi = luminance_calculate(sets.aperture[p_av_i], sets.iso[p_iso_i],
                p_shutter)

        # Values for current step
        (c_av_i, c_iso_i, c_shutter_i, c_bulb) = luminance_settings_get(r[i],
                sets.aperture, sets.iso, sets.shutter,
                iso_max=1600, bulb_min=3, shutter_min=(1/1000.))
        c_shutter = c_bulb
        if c_bulb == None:
            c_shutter = sets.shutter[c_shutter_i]
        c_lumi = luminance_calculate(sets.aperture[c_av_i], sets.iso[c_iso_i],
                c_shutter)

        if p_lumi > c_lumi:
            success = False
            print('luminance_settings_get does not act monotonically at:')
            print('l:{} (aperture:{}, iso:{}, shutter:{}, bulb:{})'.format(
                r[i-1], sets.aperture[p_av_i], sets.iso[p_iso_i],
                sets.shutter[p_shutter_i], p_bulb))
            print('l:{} (aperture:{}, iso:{}, shutter:{}, bulb:{})'.format(
                r[i], sets.aperture[c_av_i], sets.iso[c_iso_i],
                sets.shutter[c_shutter_i], c_bulb))

    return success

# Values to check for
r_scaler = 100;
r = [ 2**(x/float(r_scaler)) for x in range(-8*r_scaler, 15*r_scaler, 1) ]
sets = Canon_550D
if not check_monotonical_growth(sets, r):
    print('MONOTONICAL GROWTH TEST FAILED.')
else:
    print('Monotonical growth check succeeded.')

