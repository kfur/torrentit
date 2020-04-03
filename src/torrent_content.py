
import typing
import zipstream
import math as m
import time
import asyncio
import const

class NoActivityTimeoutError(Exception):
    pass

class Reader(typing.BinaryIO):
    def write(self, s: typing.Union[bytes, bytearray]) -> int:
        pass

    def mode(self) -> str:
        pass

    def name(self) -> str:
        pass

    def close(self) -> None:
        pass

    def closed(self) -> bool:
        pass

    def fileno(self) -> int:
        pass

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        pass

    def readable(self) -> bool:
        pass

    def readline(self, limit: int = -1) -> typing.AnyStr:
        pass

    def readlines(self, hint: int = -1) -> typing.List[typing.AnyStr]:
        pass

    def seek(self, offset: int, whence: int = 0) -> int:
        pass

    def seekable(self) -> bool:
        pass

    def tell(self) -> int:
        pass

    def truncate(self, size: int = None) -> int:
        pass

    def writable(self) -> bool:
        pass

    def write(self, s: typing.AnyStr) -> int:
        pass

    def writelines(self, lines: typing.List[typing.AnyStr]) -> None:
        pass

    def __enter__(self) -> 'typing.IO[typing.AnyStr]':
        pass

    def __exit__(self, type, value, traceback) -> None:
        pass

class ZipTorrentContentFile(Reader):
    def __init__(self, torrent_handler, files, name, progress_callback, log, should_split=True):
        self.buf = bytes()
        self.progress_callback = progress_callback
        self.log = log
        self.processed_size = 0
        self.torrent_handler = torrent_handler
        self.should_split = should_split
        # self.progress_text = None
        self.files = files
        self.files_size_sum = 0
        file_names_sum = 0
        self.zipstream = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_STORED, allowZip64=True)
        for f in files:
            self.zipstream.write_iter(f.info.fullpath, f)
            self.files_size_sum += f.info.size
            file_names_sum += len(f.info.fullpath.encode('utf'))

        #self.real_size = 21438417 + 205 + 6 #len(files) * (30 + 16 + 46) + 2 * file_names_sum + files_size_sum + 22 + 512
        self.real_size = len(files) * (30 + 16 + 46) + 2 * file_names_sum + self.files_size_sum + 22 + 5120
        self.max_size = const.TG_MAX_FILE_SIZE if should_split else self.real_size
        self.big = self.real_size > self.max_size
        self._size = self.max_size if self.big else self.real_size

        last_repl = False
        f_name = ''
        for i in name:
            if not i.isalnum():
                f_name += '_' if last_repl == False else ''
                last_repl = True
            else:
                f_name += i
                last_repl = False

        self._name = f_name
        self.zip_num = 1
        self.must_next_file = False
        self.zip_parts = m.ceil(self.real_size / const.TG_MAX_FILE_SIZE)
        self.downloaded_bytes_count = 0
        self.last_percent = -1
        self.should_close = False
        self.zipiter = iter(self.zipstream)
        self.is_finished = False
        self.last_progress_update = time.time()
        self.log.debug("ZipTorrentContentFile.real_size {} ZipTorrentContentFile.size {}".format(self.real_size, self.size))

    def set_should_split(self, should_split=True):
        self.max_size = const.TG_MAX_FILE_SIZE if should_split else self.real_size
        self.big = self.real_size > self.max_size
        self._size = self.max_size if self.big else self.real_size

    @property
    def size(self):
        if self.big:
            data_left = self.real_size - (self.zip_num - 1) * self.max_size
            if data_left > self.max_size:
                return self.max_size
            else:
                return data_left
        else:
            return self._size

    def close(self):
        self.zipstream.close()

    def closed(self):
        return False

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def flush(self):
        pass

    def isatty(self):
        return False

    def readable(self):
        return True

    def readline(self, size=-1):
        # future_data = asyncio.run_coroutine_threadsafe(self.read(), client.loop)
        # data = future_data.result()
        return None

    def readlines(self, hint=-1):
        # future_data = asyncio.run_coroutine_threadsafe(self.read(), client.loop)
        # data = future_data.result()
        return None

    def seekable(self):
        return False

    def tell(self):
        return 0

    def writable(self):
        return False

    def writelines(self, lines):
        return

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.must_next_file:
            self.must_next_file = False
            raise StopAsyncIteration

        data = await self.read(512*1024)
        if len(data) == 0 or self.processed_size == 0:
            raise StopAsyncIteration
        return data

    @property
    def name(self):
        if self.big:
            return self._name[:20]+'.zip'+'.{:03d}'.format(self.zip_num)
        else:
            return self._name + '.zip'

    async def read(self, n=-1):
        self.log.debug("Zip len read = " + str(n))
        resp = bytes()
        if len(self.buf) != 0:
            resp = self.buf
            self.buf = bytes()
        if n == -1:
            n = self.size
        if n + self.processed_size > self.max_size:
            self.log.debug('n({}) + ZipTorrentContentFile.processed_size({}) > TG_MAX_FILE_SIZE'.format(n, self.processed_size))
            n = self.max_size - self.processed_size
        elif n + self.processed_size > self.size:
            self.log.debug('n({}) + ZipTorrentContentFile.processed_size({}) > ZipTorrentContentFile.size({})'.format(n, self.processed_size, self.size))
            n = self.size - self.processed_size

        while len(resp) < n and self.processed_size < self.max_size:
            try:
                data = await next_zip_piece(self.zipiter)
                if data is None:
                    break
                resp += data

                #if time.time() - self.last_progress_update > 2:
                #    await self.event.edit(self.progress_text.format(str(m.floor((self.downloaded_bytes_count*100) / self.size))))
                #    self.last_progress_update = time.time()
                #resp += await self.zipstream.__aiter__().__next__()
                self.log.debug('new resp len = {}  n= {}'.format(len(resp), n))
                #if len(resp) == 0 and self.should_close == False:
                #    print("\nSHOULD CLOSE CALL\n")
                #    self.zipiter = iter(self.zipstream)
                #    self.should_close = True
                #    continue
            except NoActivityTimeoutError:
                self.log.info('No activity timeout')
                raise
            except Exception as e:
                #self.is_finished = True
                resp += b'\0' * (self.real_size - self.processed_size - len(resp))
                self.processed_size += len(resp)
                self.log.debug("Zip StopAsyncIteration self.buf=" + str(len(self.buf)))

                return resp

            if len(resp) > n:
                self.log.debug("len resp={} is greater then n = {}".format(len(resp), n))
                self.buf = resp[n:]
                resp = resp[0:n]
                self.log.debug("return resp len =" + str(len(resp)))


        if len(resp) != 0 and n == 0:
            # send last piece
            self.log.debug('send last piece len(resp) != 0 and n == 0')
            self.processed_size += len(resp)
            self.log.debug('ZipTorrentContentFile.processed_size = ' + str(self.processed_size))
            return resp

        if len(resp) > n:
            self.log.debug("len resp={} is greater then n = {}".format(len(resp), n))
            self.buf = resp[n:]
            resp = resp[0:n]
            self.log.debug("return resp len =" + str(len(resp)))

        self.processed_size += len(resp)

        if self.processed_size >= self.max_size:
            #if self.is_finished == False and self.real_size - self.max_size <= 0:
            #    self.real_size += 1024
            #    self.max_size = TG_MAX_FILE_SIZE if self.should_split else self.real_size
            #    self.big = self.real_size > self.max_size
            #    self.size = self.max_size if self.big else self.real_size
            #else:
            self.processed_size = 0
            self.must_next_file = True
            #self.real_size -= self.max_size
            # self._size = self.max_size if self.real_size > self.max_size else self.real_size

        self.log.debug('ZipTorrentContentFile.processed_size = ' + str(self.processed_size))
        if n <= 1024 and n > 0:
            resp += b'\0'*(n-len(resp))
            self.processed_size += len(resp)

        self.downloaded_bytes_count += len(resp)
        if self.real_size != 0:
            perc = m.floor((self.downloaded_bytes_count*100) / self.real_size)
            if perc != self.last_percent:
                try:
                    self.log.info('Progress {}%'.format(perc))
                    self.last_percent = perc
                    await self.progress_callback(perc)
                    # await self.event.edit(self.progress_text.format(perc), buttons=[Button.inline('Cancel', str(self.event.sender_id))])
                except Exception as e:
                    self.log.error(e)

        return resp

# async def _progress(progress_callback, piece):
#     await progress_callback(piece)

class TorrentContentFile(Reader):
    def __init__(self, torrent_handler, file_info, log):
        self.buf = bytes()
        self.torrent_handler = torrent_handler
        self.cur_piece = 0
        self.info = file_info
        self.log = log
        # self.progress_callback = progress_callback
        self.downloaded_size = 0
        self.no_actity_timeout = 300
        self.no_actity_elapsed_time = 0
        self.last_task = None
        self.last_progress_time = time.time()
        self.log.debug("New TorrentContentFile self.num_piece = {} self.size = {}".format(self.info.num_pieces, self.info.size))

    #async def read(self, n: int = -1) -> bytes:
    def read(self, n: int = -1) -> bytes:
        self.log.debug("read " + str(n) + " bytes")
        resp = bytes()
        if len(self.buf) != 0:
            self.log.debug('len TorrentContentFile.buf = {} != 0'.format(len(self.buf)))
            resp = self.buf
            self.buf = bytes()
        if n == -1:
            n = self.torrent_handler.piece_size()
        #while len(resp) < n and self.cur_piece < self.info.num_pieces:
        while len(resp) < n and (self.downloaded_size + len(resp)) != self.info.size:
            piece = self.torrent_handler.next_piece()
            self.log.debug('len TorrentContentFile.torrent_handle.next_piece() = ' + str(len(piece)))

            if len(piece) == 0:
                self.log.debug("No pieces. Peers = " + str(self.torrent_handler.status().num_peers) + "; Elapsed time = " + str(self.no_actity_elapsed_time))
                #await asyncio.sleep(3)
                self.no_actity_elapsed_time += 3
                time.sleep(3)
                if self.no_actity_elapsed_time >= self.no_actity_timeout:
                    raise NoActivityTimeoutError
                continue
            else:
                self.no_actity_elapsed_time = 0
                resp += piece
                self.cur_piece += 1
                #if time.time() - self.last_progress_time > 2:
                #progress_task = client.loop.create_task(_progress(self.progress_callback, self.cur_piece))
                    #self.progress_callback(self.cur_piece)
                    #future_data = asyncio.run_coroutine_threadsafe(self.progress_callback(self.cur_piece), client.loop)
                    #data = future_data.result()
                    #self.last_progress_time = time.time()

        if len(resp) > n:
            self.log.debug('TorrentContentFile resp = {} > n = {}'.format(len(resp), n))
            self.buf = resp[n:]
            resp = resp[0:n]

        self.downloaded_size += len(resp)
        self.log.debug('TorrentContentFile.downloaded_size = ' + str(self.downloaded_size))
        self.log.debug("TorrentContentFile return resp " + str(len(resp)))
        return resp

    def is_complete(self):
        is_c = self.downloaded_size == self.info.size
        if self.downloaded_size > self.info.size:
            self.log.warning('LOGIC ERROR TorrentContentFile.downloaded_size = {}  TorrentContentFile.info.size = {}'.format(self.downloaded_size, self.info.size))
        if is_c:
            self.log.debug('COMPLETE TorrentContentFile.downloaded_size = {}  TorrentContentFile.info.size = {}'.format(self.downloaded_size, self.info.size))
        return is_c

    #async def __aiter__(self):
    def __iter__(self):
        return self

    #async def __anext__(self):
    def __next__(self):
        #b = await self.read()
        b = self.read()
        if len(b) == 0:
            self.log.debug('TorrentContentFile StopIteration self.buf = ' + str(len(self.buf)))
            raise StopIteration()
        else:
            return b


class AsyncTorrentContentFileWrapper(Reader):
    def __init__(self, torrent_content, progress_callback, uploaded_sum, files_size_sum, log):
        self.tc = torrent_content
        # self.event = event
        # self.progress_text = progress_text
        self.progress_callback = progress_callback
        self.uploaded_sum = uploaded_sum
        self.files_size_sum = files_size_sum
        self.last_percent = -1
        self.log = log

    async def read(self, n: int = -1) -> bytes:
        self.log.debug("read " + str(n) + " bytes")
        resp = bytes()
        if len(self.tc.buf) != 0:
            self.log.debug('len(AsyncTorrentContentFileWrapper.tc.buf) = {} != 0'.format(len(self.tc.buf)))
            resp = self.tc.buf
            self.tc.buf = bytes()
        if n == -1:
            n = self.tc.torrent_handler.piece_size()
        #while len(resp) < n and self.tc.cur_piece < self.tc.info.num_pieces:
        while len(resp) < n and (self.tc.downloaded_size + len(resp)) != self.tc.info.size:
            piece = self.tc.torrent_handler.next_piece()
            self.log.debug('len AsyncTorrentContentFileWrapper.tc.torrent_handle.next_piece() = ' + str(len(piece)))

            if len(piece) == 0:
                self.log.debug("No pieces. Peers = " + str(self.tc.torrent_handler.status().num_peers) + "; Elapsed time = " + str(self.tc.no_actity_elapsed_time))
                self.tc.no_actity_elapsed_time += 3
                await asyncio.sleep(3)
                if self.tc.no_actity_elapsed_time >= self.tc.no_actity_timeout:
                    raise NoActivityTimeoutError
                continue
            else:
                self.tc.no_actity_elapsed_time = 0
                resp += piece
                self.tc.cur_piece += 1
                #if time.time() - self.tc.last_progress_time > 2:
                #progress_task = client.loop.create_task(_progress(self.tc.progress_callback, self.tc.cur_piece))
                    #self.tc.progress_callback(self.tc.cur_piece)
                    #future_data = asyncio.run_coroutine_threadsafe(self.tc.progress_callback(self.tc.cur_piece), client.loop)
                    #data = future_data.result()
                    #self.tc.last_progress_time = time.time()

        if len(resp) > n:
            self.log.debug('resp = {} > n = {}'.format(len(resp), n))
            self.tc.buf = resp[n:]
            resp = resp[0:n]

        self.tc.downloaded_size += len(resp)

        perc = m.floor(((self.tc.downloaded_size + self.uploaded_sum) *100) / self.files_size_sum)
        if perc != self.last_percent:
            self.log.info('Progress {}%'.format(perc))
            try:
                self.last_percent = perc
                await self.progress_callback(perc)
                # await self.event.edit(self.progress_text.format(perc), buttons=[Button.inline('Cancel', str(self.event.sender_id))])
            except Exception as e:
                self.log.error(e)

        self.log.debug('AsyncTorrentContentFileWrapper.tc.downloaded_size = ' + str(self.tc.downloaded_size))
        self.log.debug("return resp " + str(len(resp)))
        return resp

    def close(self):
        self.zipstream.close()

    def closed(self):
        return False

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def flush(self):
        pass

    def isatty(self):
        return False

    def readable(self):
        return True

    def readline(self, size=-1):
        # future_data = asyncio.run_coroutine_threadsafe(self.read(), client.loop)
        # data = future_data.result()
        return None

    def readlines(self, hint=-1):
        # future_data = asyncio.run_coroutine_threadsafe(self.read(), client.loop)
        # data = future_data.result()
        return None

    def seekable(self):
        return False

    def tell(self):
        return 0

    def writable(self):
        return False

    def writelines(self, lines):
        return

    def __aiter__(self):
        return self

    async def __anext__(self):
        b = await self.read()
        if len(b) == 0:
            self.log.debug('TorrentContentFile StopAsyncIteration self.buf = ' + str(len(self.tc.buf)))
            raise StopAsyncIteration()
        else:
            return b

def _next_zip_piece(zipstream):
    r = None
    try:
        r = next(zipstream)
    except StopIteration as e:
        print(e)

    return r

@asyncio.coroutine
def next_zip_piece(zipstream):
    # piece = yield from client.loop.run_in_executor(None, _next_zip_piece, zipstream)
    piece = yield from asyncio.get_event_loop().run_in_executor(None, _next_zip_piece, zipstream)

    return piece
