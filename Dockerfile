FROM ubuntu:18.04

COPY build-lt.sh /root/
RUN chmod +x /root/build-lt.sh && /root/build-lt.sh


FROM ubuntu:20.04

WORKDIR /root/torrentit
ENV LD_LIBRARY_PATH /root/torrentit
COPY requirements.txt .
COPY src/*.py ./
COPY start.sh .
COPY pyston_2.1_20.04.deb . 
COPY --from=0 /root/boost_1_64_0/bin.v2/libs/python/build/gcc-7/release/asserts-production/i2p-off/libtorrent-link-static/libtorrent-python-pic-on/lt-visibility-hidden/libboost_python3.so.1.64.0  .
COPY --from=0 /root/libtorrent/bindings/python/bin/gcc-7/release/asserts-production/i2p-off/libtorrent-link-static/libtorrent-python-pic-on/lt-visibility-hidden/libtorrent.so .

RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends fontconfig-config fonts-dejavu-core libbsd0 libexpat1 libfontconfig1 libfreetype6 libgdbm6 libpng16-16 libreadline8 libsqlite3-0 libtcl8.6 libtk8.6 libx11-6 libx11-data libxau6 libxcb1 libxdmcp6 libxext6 libxft2 libxrender1 libxss1 readline-common tk8.6-blt2.5 tzdata ucf x11-common openssl git build-essential libssl-dev libffi-dev
RUN dpkg -i pyston_2.1_20.04.deb
RUN pyston -m pip install wheel
RUN pyston -m pip install -r requirements.txt && chmod +x ./start.sh && chmod +x main.py
RUN apt remove -y build-essential && apt autoremove -y
RUN rm -rf /var/lib/apt/lists/*
RUN apt update && apt install -y libjemalloc2
ENV LD_PRELOAD /usr/lib/x86_64-linux-gnu/libjemalloc.so.2

CMD ["./start.sh"]
