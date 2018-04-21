import subprocess as sub
from time import sleep, time
from os import O_NONBLOCK, read, lseek, SEEK_END
from fcntl import fcntl, F_GETFL, F_SETFL
from datetime import datetime

_debug_file=None

def gph_debug_set(fh):
    global _debug_file

    if _debug_file != None:
        _debug_file.close()

    _debug_file = fh

def gph_debug_open(fname):
    global _debug_file

    if _debug_file != None:
        _debug_file.close()

    _debug_file = open(fname, 'a', buffering=1)

def _debug_write(inf):
    if _debug_file == None or len(inf) == 0:
        return
    n=datetime.now().isoformat() + ': '
    _debug_file.write(inf.replace('\n', '\n'+n))

# Convinience function for shooting a picture with arbitary exposure
def gph_shoot(exposure=1):
    gph_cmd('set-config-index /main/actions/eosremoterelease=2') # Press Full
    sleep(exposure)
    gph_cmd('set-config-index /main/actions/eosremoterelease=4') # Release Full
    gph_cmd('wait-event-and-download 4s', timeout=4.5) # Should download the image


gph = None

def gph_check_stderr():
    try:
        err = read(gph.stderr.fileno(), 1024)
        if len(err) != 0:
            _debug_write(err)
            print('Gphoto2 printed to stderr:')
            print(err)
        True
    except OSError:
        False


def gph_open():
    global gph
    gph = sub.Popen(['gphoto2','--shell'], stdout=sub.PIPE, stderr=sub.PIPE,
            stdin=sub.PIPE)

    # We don't like it when the process exits unexpectedly.
    fcntl(gph.stdout, F_SETFL, O_NONBLOCK)
    fcntl(gph.stderr, F_SETFL, O_NONBLOCK)

    # See what's what on the initialisation

    totslept=0.0
    timeout=3.0
    while totslept < timeout:
        try:
            o = read(gph.stdout.fileno(), 10024)
            _debug_write(o)
            if 'gphoto2:' == o[0:8]:
                break
            print('Gphoto2 stdout not prompt:')
            print(o)
            gph_check_stderr()
            exit(1)
        except OSError:
            sleep(0.1)
            totslept+=0.1

    if gph_check_stderr() == True:
        exit(1)
    if totslept >= timeout:
        print('Gphoto2 stdout did not give a prompt in time.')
        exit(1)


def gph_close():
    gph.stdin.close()
    gph.wait()

def gph_reload():
    gph_close()
    gph_open()

def gph_cmd(cmd, timeout=2):
    if gph.stdin.closed:
        print('Gphoto2 failed somehow (stdin closed).')
        exit(0)
    if gph.stdout.closed:
        print('Gphoto2 failed somehow (stdin closed).')
        exit(0)

    # If there's some rubbish ahead, ignore it.
    rubbish=''
    try:
        add=read(gph.stdout.fileno(), 1024)
        _debug_write(add)
        while add != '':
            rubbish+=add
            add=read(gph.stdout.fileno(), 1024)
            _debug_write(add)
    except OSError:
        pass

    if len(rubbish) != 0:
        print('Following rubbish was dangling gphoto2 buffer: "%s"' % rubbish)
        rubbish=''

    gph.stdin.write(cmd + '\n')
    gph.stdin.flush()
    _debug_write(cmd + '\n')

    t_begin = time()
    t_wait = t_begin + float(timeout)
    t_wait_original = t_wait
    answ=''
    answ_chk=0

    n_of_failures=0
    while len(answ) == 0 or 'gphoto2:' not in answ[answ_chk:]:
        try:
            answ_chk=len(answ) - 8
            if answ_chk < 0:
                answ_chk = 0
            r=read(gph.stdout.fileno(), 4192)
            _debug_write(answ)
            answ+=r
        except OSError:
            t_now = time()
            if t_now > t_wait:
                print('Getting back to gphoto2 cmd late by %.2f:' % (t_now - t_wait_original))
                print(answ)
                if n_of_failures == 0:
                    t_wait += 25.0
                    print('Waiting for %.2f more..' % (t_wait - t_now))
                    n_of_failures+=1
                    continue
                else: # Last-ditch effort
                    print('Reloading gphoto2 command line.')
                    gph_close()
                    sleep(0.1)
                    gph_open()
                    sleep(0.1)
                    model=gph_cmd('get-config /main/status/cameramodel')
                    if len(model) == 0:
                        print('Failed getting camera model, reloading once again..')
                        sleep(0.1)
                        gph_close()
                        sleep(0.1)
                        gph_open()
                        sleep(0.1)
                    print(model[2])

                    #exit(0)
            sleep(0.1)
            continue

    if n_of_failures != 0:
        t_now = time()
        print('Got back to prompt %.2f overdue.' % (time() - t_wait_original))

    return answ.split('\n')[2:-1]

