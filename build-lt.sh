#!/bin/bash
set -e

apt update && apt upgrade -y
apt install -y build-essential git wget python3-dev

cd /root/
wget 'https://dl.bintray.com/boostorg/release/1.64.0/source/boost_1_64_0.tar.gz'
echo "Unziping boost..."
tar xzf boost_1_64_0.tar.gz
export BOOST_BUILD_PATH="/root/boost_1_64_0/tools/build"
export BOOST_ROOT="/root/boost_1_64_0"

cd $BOOST_ROOT
./bootstrap.sh
export PATH="${PATH}:${BOOST_BUILD_PATH}/src/engine/bin.linuxx86_64"
cp ${BOOST_BUILD_PATH}/example/user-config.jam ${BOOST_BUILD_PATH}/
printf "using gcc ;\nusing python : 3.6 : /usr/bin/python3 : /usr/include/python3.6 : /usr/lib/python3.6 ;" \
> ${BOOST_BUILD_PATH}/user-config.jam

cd /root
git clone 'https://github.com/kfur/libtorrent'
cd /root/libtorrent/bindings/python
CXXFLAGS="-Ofast -DNDEBUG -DTORRENT_DISABLE_GEO_IP -DTORRENT_DISABLE_RESOLVE_COUNTRIES -DTORRENT_DISABLE_INVARIANT_CHECKS -DTORRENT_PRODUCTION_ASSERTS=1" \
LDFLAGS="-s" \
bjam libtorrent-link=static variant=release i2p=off asserts=production debug-symbols=off optimization=speed -j2
