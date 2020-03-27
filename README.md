# torrentit
Telegram bot for download torrents without persistent storage.
Torrents content can be stored into telegram or temporarily in fex.net.

# Dependencies
Python3 dependencies install via `pip3 install -r requirements.txt`

# Build
Run `./build-lt.sh` script to build libtorrent. Then copy `./boost_1_64_0/bin.v2/libs/python/build/gcc-7/release/asserts-production/i2p-off/libtorrent-link-static/libtorrent-python-pic-on/lt-visibility-hidden/libboost_python3.so.1.64.0` and `libtorrent/bindings/python/bin/gcc-7/release/asserts-production/i2p-off/libtorrent-link-static/libtorrent-python-pic-on/lt-visibility-hidden/libtorrent.so` to project dir.

# Running
Run `cd src; python3 main.py`.
For running required phone number for bypassing telegram bot api upload files limitation to 50 MB.

Set the following enviroment variables:
  1. Bot token(from Bot Father):
`BOT_TOKEN`

  2. Chat id between bot and agent (client id with phone number):
`BOT_AGENT_CHAT_ID`

  3. Chat id between agent and bot (bot name):
`BOT_ID`

  4. Api id (https://core.telegram.org/api/obtaining_api_id):
`API_ID`
  5. Api hash (https://core.telegram.org/api/obtaining_api_id):
`API_HASH`
