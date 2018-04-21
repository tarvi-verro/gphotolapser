
# Maintainer: Your Name <youremail@domain.com>
pkgname=gphotolapser
pkgver=0.11
pkgrel=1
epoch=
pkgdesc="Record a timelapse with a DSLR."
arch=('any')
url=""
license=('GPL')
depends=('python2' 'python2-future' 'python2-exiv2'
         'python2-numpy' 'python2-pillow' 'gphoto2>=2.5.15')
source=('setup.py')
md5sums=('SKIP')

prepare() {
	ln -fs ../gphotolapser
	ln -fs ../bin
}

package() {
        python2 setup.py install --root=$pkgdir/ --optimize=1
	mkdir -p $pkgdir/etc/
	python2 -c "import gphotolapser.configs as cfg; cfg.cfg_write(f='$pkgdir/etc/gphotolapser.conf', signalservice=False);"
}

