
# Maintainer: Your Name <youremail@domain.com>
pkgname=gphotolapser
pkgver=0.8
pkgrel=1
epoch=
pkgdesc="Record a timelapse with a DSLR."
arch=('any')
url=""
license=('GPL')
depends=('python2' 'python2-future' 'python2-exiv2'
         'python2-numpy' 'python2-pillow' 'gphoto2')
source=('setup.py')
md5sums=('SKIP')

prepare() {
	ln -s ../gphotolapser
}

package() {
        python2 setup.py install --root=$pkgdir/ --optimize=1
}

