FROM ubuntu:18.04

COPY build-lt.sh /root/
RUN chmod +x /root/build-lt.sh && /root/build-lt.sh


FROM python:3.8-buster

WORKDIR /root/torrentit
ENV LD_LIBRARY_PATH /root/torrentit
COPY requirements.txt .
COPY src/*.py ./
COPY start.sh .
COPY --from=0 /root/boost_1_64_0/bin.v2/libs/python/build/gcc-7/release/asserts-production/i2p-off/libtorrent-link-static/libtorrent-python-pic-on/lt-visibility-hidden/libboost_python3.so.1.64.0  .
COPY --from=0 /root/libtorrent/bindings/python/bin/gcc-7/release/asserts-production/i2p-off/libtorrent-link-static/libtorrent-python-pic-on/lt-visibility-hidden/libtorrent.so .

RUN pip3 install -r requirements.txt && chmod +x ./start.sh && chmod +x main.py
RUN apt update && apt install -y libjemalloc2
ENV LD_PRELOAD /usr/lib/x86_64-linux-gnu/libjemalloc.so.2

CMD ["./start.sh"]
