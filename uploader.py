__version__ = (2, 0, 1)

# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://img.icons8.com/stickers/500/000000/upload.png
# meta developer: @hikarimods
# scope: hikka_only

import imghdr
import io
import logging
import random
import re
import os

import requests
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.types import Message

from .. import loader, utils, main

logger = logging.getLogger(__name__)


@loader.tds
class FileUploaderMod(loader.Module):
    """Different engines file uploader"""

    strings = {
        "name": "Uploader",
        "uploading": "🚀 <b>Uploading...</b>",
        "noargs": "🚫 <b>No file specified</b>",
        "err": "🚫 <b>Upload error</b>",
        "uploaded": '🎡 <b>File <a href="{0}">uploaded</a></b>!\n\n<code>{0}</code>',
        "imgur_blocked": "🚫 <b>Unban @ImgUploadBot</b>",
        "not_an_image": "🚫 <b>This platform only supports images</b>",
    }

    strings_ru = {
        "uploading": "🚀 <b>Загрузка...</b>",
        "noargs": "🚫 <b>Файл не указан</b>",
        "err": "🚫 <b>Ошибка загрузки</b>",
        "uploaded": '🎡 <b>Файл <a href="{0}">загружен</a></b>!\n\n<code>{0}</code>',
        "imgur_blocked": "🚫 <b>Разблокируй @ImgUploadBot</b>",
        "not_an_image": "🚫 <b>Эта платформа поддерживает только изображения</b>",
        "_cmd_doc_imgur": "Загрузить на imgur.com",
        "_cmd_doc_oxo": "Загрузить на 0x0.st",
        "_cmd_doc_x0": "Загрузить на x0.at",
        "_cmd_doc_skynet": "Загрузить на децентрализованную платформу SkyNet",
        "_cls_doc": "Загружает файлы на различные хостинги",
    }

    async def client_ready(self, client, db):
        self._client = client
        if "OKTETO" not in os.environ:
            # x0.at is temporarily disabled
            # self.x0cmd = self.x0cm_
            self.oxocmd = self.oxocm_

    async def get_media(self, message: Message):
        reply = await message.get_reply_message()
        m = None
        if reply and reply.media:
            m = reply
        elif message.media:
            m = message
        elif not reply:
            await utils.answer(message, self.strings("noargs"))
            return False

        if not m:
            file = io.BytesIO(bytes(reply.raw_text, "utf-8"))
            file.name = "file.txt"
        else:
            file = io.BytesIO(
                (
                    await self.fast_download(
                        m.document if main.__version__ < (1, 1, 28) else m,
                        message_object=message,
                    )
                ).getvalue()
            )
            file.name = (
                m.file.name
                or (
                    "".join(
                        [
                            random.choice("abcdefghijklmnopqrstuvwxyz1234567890")
                            for _ in range(16)
                        ]
                    )
                )
                + m.file.ext
            )

        return file

    async def get_image(self, message: Message):
        file = await self.get_media(message)
        if not file:
            return False

        if imghdr.what(file) not in ["gif", "png", "jpg", "jpeg", "tiff", "bmp"]:
            await utils.answer(message, self.strings("not_an_image"))
            return False

        return file

    async def x0cm_(self, message: Message):
        """Upload to x0.at"""
        message = await utils.answer(message, self.strings("uploading"))
        file = await self.get_media(message)
        if not file:
            return

        try:
            x0at = await utils.run_sync(
                requests.post,
                "https://x0.at",
                files={"file": file},
            )
        except ConnectionError:
            await utils.answer(message, self.strings("err"))
            return

        url = x0at.text
        await utils.answer(message, self.strings("uploaded").format(url))

    async def skynetcmd(self, message: Message):
        """Upload to decentralized SkyNet"""
        message = await utils.answer(message, self.strings("uploading"))
        file = await self.get_media(message)
        if not file:
            return

        try:
            skynet = await utils.run_sync(
                requests.post,
                "https://siasky.net/skynet/skyfile",
                files={"file": file},
            )
        except ConnectionError:
            await utils.answer(message, self.strings("err"))
            return

        await utils.answer(
            message,
            self.strings("uploaded").format(
                f"https://siasky.net/{skynet.json()['skylink']}"
            ),
        )

    async def imgurcmd(self, message: Message):
        """Upload to imgur.com"""
        message = await utils.answer(message, self.strings("uploading"))
        file = await self.get_image(message)
        if not file:
            return

        chat = "@ImgUploadBot"

        async with self._client.conversation(chat) as conv:
            try:
                m = await conv.send_message(file=file)
                response = await conv.get_response()
            except YouBlockedUserError:
                await utils.answer(message, self.strings("imgur_blocked"))
                return

            await m.delete()
            await response.delete()

            try:
                url = (
                    re.search(
                        r'<meta property="og:image" data-react-helmet="true" content="(.*?)"',
                        (await utils.run_sync(requests.get, response.raw_text)).text,
                    )
                    .group(1)
                    .split("?")[0]
                )
            except Exception:
                url = response.raw_text

            await utils.answer(message, self.strings("uploaded").format(url))

    async def oxocm_(self, message: Message):
        """Upload to 0x0.st"""
        message = await utils.answer(message, self.strings("uploading"))
        file = await self.get_media(message)
        if not file:
            return

        try:
            oxo = await utils.run_sync(
                requests.post,
                "https://0x0.st",
                files={"file": file},
            )
        except ConnectionError:
            await utils.answer(message, self.strings("err"))
            return

        url = oxo.text
        await utils.answer(message, self.strings("uploaded").format(url))
