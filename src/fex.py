
import json
import aiohttp
import os
from dataclasses import dataclass
import typing


class FexUploader():

    def __init__(self, log):
        self.token = None
        self.log = log
        self.dirtree = dict()
        self.session = aiohttp.ClientSession()
        self.download_link = None

    async def delete(self):
        await self.session.close()

    @classmethod
    async def new(cls, log):
        fu = FexUploader(log)
        an_resp = await fu.session.get('https://api.fex.net/api/v1/config/anonymous')
        anon_data = json.loads(await an_resp.read())

        fu.token = anon_data['anonymous']['anonym_token']

        return fu

    async def create_dir(self, name, parent_id=-1):
        # name - exact dir name
        self.log.debug('create dir with name = ' + name)
        header = {
            'authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json'
        }
        dat = '{"names": ["'+name+'"]}'
        dir_create_resp = await self.session.post('https://api.fex.net/api/v1/anonymous/directory/'+(str(parent_id) if parent_id != -1 else ""), data=dat, headers=header)
        dir_data = json.loads(await dir_create_resp.read())

        id = dir_data['data'][0]['id']
        self.dirtree[name] = id
        return id

    async def get_dir_id(self, fullpath):
        self.log.debug('get dir id for path = ' + fullpath)
        # name - full dir path
        if len(fullpath) == 0 or fullpath == '/':
            return -1
        if fullpath[-1] == '/':
            fullpath = fullpath[:len(fullpath)-1]
        if fullpath in self.dirtree:
            return self.dirtree[fullpath]

        dir = os.path.basename(fullpath)
        parent_dir_id = await self.get_dir_id(fullpath[:len(fullpath) - len(dir)])

        dir_id = await self.create_dir(dir, parent_dir_id)
        self.dirtree[fullpath] = dir_id

        return dir_id

    async def add_file(self, name, size, file):
        file_name = os.path.basename(name)
        file_path = name[:len(name) - len(file_name)]
        dir_id = await self.get_dir_id(file_path)
        location = await self.create_file_location(file_name, size, dir_id)
        header = {
            'authorization': 'Bearer ' + self.token,
            'fsp-version': '1.0.0',
            'fsp-offset': '0',
            'fsp-size': str(size),
        }
        await self.session.post(location, headers=header)
        create_resp = await self.session.patch(location, data=file, headers=header, timeout=14400)
        create_d = await create_resp.read()
        create = json.loads(create_d)
        self.log.debug(create)

    async def create_file_location(self, name, size, dir_id=-1):
        header = {
            'authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json'
        }
        dat = '{"directory_id":'+('null' if dir_id == -1 else str(dir_id))+',"size":' + str(size) + ',"name":"' + name + '"}'
        data_resp = await self.session.post('https://api.fex.net/api/v1/anonymous/file', data=dat, headers=header)
        data = json.loads(await data_resp.read())
        self.log.debug(data)
        self.download_link = 'https://fex.net/s/'+data['anon_upload_link']
        return data['location']

    async def upload_files(self, files):
        uploaded_sum = 0
        for f in files:
            self.log.info('upload file ' + f.path)
            await self.add_file(f.path, f.size, f.file)
            uploaded_sum += f.size

@dataclass
class FexFile:
        file: typing.BinaryIO
        path: str
        size: int
