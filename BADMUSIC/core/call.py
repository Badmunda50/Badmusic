import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, filters
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
)
from ntgcalls import TelegramServerError
from pytgcalls.types import (
    GroupCallParticipant,
    MediaStream,
    ChatUpdate, 
    Update,
)
from pytgcalls.types import (
    AudioQuality, 
    VideoQuality,
)

from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pytgcalls.exceptions import InvalidMTProtoClient
from pytgcalls.types.stream import StreamAudioEnded

import config
from strings import get_string
from BADMUSIC import LOGGER, Platform, app
from BADMUSIC.misc import db
from BADMUSIC.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_assistant,
    get_audio_bitrate,
    get_lang,
    get_loop,
    get_video_bitrate,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from BADMUSIC.utils.exceptions import AssistantErr
from BADMUSIC.utils.formatters import check_duration, seconds_to_min, speed_converter
from BADMUSIC.utils.inline.play import stream_markup, telegram_markup
from BADMUSIC.utils.stream.autoclear import auto_clean
from BADMUSIC.utils.thumbnails import gen_thumb


autoend = {}
counter = {}


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)



class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(
            name="PROAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(
            self.userbot1,
            cache_duration=100,
        )
        # Add the try-except block for initializing vc
        try:
            self.vc = PyTgCalls(self.userbot1)
        except InvalidMTProtoClient:
            print("Invalid MTProto Client. Please check the configuration of your userbot instance.")
            raise
        self.vc_users = {}

        self.userbot2 = Client(
            name="PROAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.two = PyTgCalls(
            self.userbot2,
            cache_duration=100,
        )
        self.userbot3 = Client(
            name="BadAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.three = PyTgCalls(
            self.userbot3,
            cache_duration=100,
        )
        self.userbot4 = Client(
            name="BadAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.four = PyTgCalls(
            self.userbot4,
            cache_duration=100,
        )
        self.userbot5 = Client(
            name="BadAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )
        self.five = PyTgCalls(
            self.userbot5,
            cache_duration=100,
        )
      

    # Add the track_vc method within the Call class
    async def track_vc(self, client: PyTgCalls, update: Update):
        global vc_users
        chat_id = update.chat_id

        # Ensure the PyTgCalls client is started
        if not hasattr(self.vc, '_started') or not self.vc._started:
            try:
                await self.vc.start()
            except PyTgCallsAlreadyRunning:
                pass  # Handle the already running case

        participants = await self.vc.get_participants(chat_id)
        current_users = {p.user_id: p for p in participants}

        for user_id, user in current_users.items():
            if user_id not in self.vc_users:
                first_name = user.user.first_name if user.user.first_name else "Unknown"
                username = f"@{user.user.username}" if user.user.username else "No Username"
                message = f"🎙 **User Joined VC**\n👤 **Name:** {first_name}\n🔹 **Username:** {username}\n🆔 **ID:** `{user_id}`"
                await app.send_message(chat_id, message)

        for user_id in list(self.vc_users.keys()):
            if user_id not in current_users:
                user = self.vc_users[user_id]
                first_name = user.user.first_name if user.user.first_name else "Unknown"
                username = f"@{user.user.username}" if user.user.username else "No Username"
                message = f"🚫 **User Left VC**\n👤 **Name:** {first_name}\n🔹 **Username:** {username}\n🆔 **ID:** `{user_id}`"
                await app.send_message(chat_id, message)

        self.vc_users = current_users
        
        
    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_call(chat_id)
        except:
            pass

    async def stop_stream_force(self, chat_id: int):
        try:
            if config.STRING1:
                await self.one.leave_call(chat_id)
        except:
            pass
        try:
            if config.STRING2:
                await self.two.leave_call(chat_id)
        except:
            pass
        try:
            if config.STRING3:
                await self.three.leave_call(chat_id)
        except:
            pass
        try:
            if config.STRING4:
                await self.four.leave_call(chat_id)
        except:
            pass
        try:
            if config.STRING5:
                await self.five.leave_call(chat_id)
        except:
            pass
        try:
            await _clear_(chat_id)
        except:
            pass

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != str("1.0"):
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == str("0.5"):
                    vs = 2.0
                if str(speed) == str("0.75"):
                    vs = 1.35
                if str(speed) == str("1.5"):
                    vs = 0.68
                if str(speed) == str("2.0"):
                    vs = 0.5
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            else:
                pass
        else:
            out = file_path
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        stream = (
            MediaStream(
                out,
                AudioQuality.STUDIO,
                VideoQuality.HD_720p,
                ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
            if playing[0]["streamtype"] == "video"
            else MediaStream(
                out,
                AudioQuality.STUDIO,
                ffmpeg_parameters=f"-ss {played} -to {duration}",
                video_flags=MediaStream.Flags.IGNORE,
            )
        )
        if str(db[chat_id][0]["file"]) == str(file_path):
            await assistant.play(chat_id, stream)
        else:
            raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_call(chat_id)
        except:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        if video:
            stream = MediaStream(
                link,
                AudioQuality.STUDIO,
                VideoQuality.HD_720p,
            )
        else:
            stream = MediaStream(
                link, 
                AudioQuality.STUDIO,
                video_flags=MediaStream.Flags.IGNORE,
            )
        await assistant.play(
            chat_id,
            stream,
        )

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        stream = (
            MediaStream(
                file_path,
                AudioQuality.STUDIO,
                VideoQuality.HD_720p,
                ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
            if mode == "video"
            else MediaStream(
                file_path,
                AudioQuality.STUDIO,
                ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
                video_flags=MediaStream.Flags.IGNORE,
            )
        )
        await assistant.play(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        await assistant.play(
            config.LOG_GROUP_ID,
            MediaStream(link),
        )
        await asyncio.sleep(0.2)
        await assistant.leave_call(config.LOGGER_ID)

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)
        if video:
            stream = MediaStream(
                link,
                AudioQuality.STUDIO,
                VideoQuality.HD_720p,
            )
        else:
            stream = (
                MediaStream(
                    link,
                    AudioQuality.STUDIO,
                    VideoQuality.HD_720p,
                )
                if video
                else MediaStream(
                    link, 
                    AudioQuality.STUDIO,
                    video_flags=MediaStream.Flags.IGNORE,
                )
            )
        try:
            await assistant.play(
                chat_id,
                stream,
            )
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            if not check:
                await _clear_(chat_id)
                return await client.leave_call(chat_id)
        except:
            try:
                await _clear_(chat_id)
                return await client.leave_call(chat_id)
            except:
                return
        else:
            queued = check[0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            db[chat_id][0]["played"] = 0
            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = True if str(streamtype) == "video" else False
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if video:
                    stream = MediaStream(
                        link,
                        AudioQuality.STUDIO,
                        VideoQuality.HD_720p,
                    )
                else:
                    stream = MediaStream(
                        link,
                        AudioQuality.STUDIO,
                        video_flags=MediaStream.Flags.IGNORE,
                    )
                try:
                    await client.play(chat_id, stream)
                except Exception:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                img = await gen_thumb(videoid)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True if str(streamtype) == "video" else False,
                    )
                except:
                    return await mystic.edit_text(
                        _["call_6"], disable_web_page_preview=True
                    )
                if video:
                    stream = MediaStream(
                        file_path,
                        AudioQuality.STUDIO,
                        VideoQuality.HD_720p,
                    )
                else:
                    stream = MediaStream(
                        file_path,
                        AudioQuality.STUDIO,
                        video_flags=MediaStream.Flags.IGNORE,
                    )
                try:
                    await client.play(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                img = await gen_thumb(videoid)
                button = stream_markup(_, chat_id)
                await mystic.delete()
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            elif "index_" in queued:
                stream = (
                    MediaStream(
                        videoid,
                        AudioQuality.STUDIO,
                        VideoQuality.HD_720p,
                    )
                    if str(streamtype) == "video"
                    else MediaStream(
                        videoid, 
                        AudioQuality.STUDIO,
                        video_flags=MediaStream.Flags.IGNORE,
                    )
                )
                try:
                    await client.play(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=config.STREAM_IMG_URL,
                    caption=_["stream_2"].format(user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                if video:
                    stream = MediaStream(
                        queued,
                        AudioQuality.STUDIO,
                        VideoQuality.HD_720p,
                    )
                else:
                    stream = MediaStream(
                        queued,
                        AudioQuality.STUDIO,
                        video_flags=MediaStream.Flags.IGNORE,
                    )
                try:
                    await client.play(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if videoid == "telegram":
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.TELEGRAM_AUDIO_URL
                        if str(streamtype) == "audio"
                        else config.TELEGRAM_VIDEO_URL,
                        caption=_["stream_1"].format(
                            config.SUPPORT_GROUP, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                elif videoid == "soundcloud":
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.SOUNCLOUD_IMG_URL,
                        caption=_["stream_1"].format(
                            config.SUPPORT_GROUP, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                else:
                    img = await gen_thumb(videoid)
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{videoid}",
                            title[:23],
                            check[0]["dur"],
                            user,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"

    async def ping(self):
        pings = []
        if config.STRING1:
            pings.append(self.one.ping)
        if config.STRING2:
            pings.append(self.two.ping)
        if config.STRING3:
            pings.append(self.three.ping)
        if config.STRING4:
            pings.append(self.four.ping)
        if config.STRING5:
            pings.append(self.five.ping)
        return str(round(sum(pings) / len(pings), 3))
    
    
    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1:
            await self.one.start()
        if config.STRING2:
            await self.two.start()
        if config.STRING3:
            await self.three.start()
        if config.STRING4:
            await self.four.start()
        if config.STRING5:
            await self.five.start()

    
    async def decorators(self):
        @self.one.on_update(filters.chat_update(ChatUpdate.Status.KICKED))
        @self.two.on_update(filters.chat_update(ChatUpdate.Status.KICKED))
        @self.three.on_update(filters.chat_update(ChatUpdate.Status.KICKED))
        @self.four.on_update(filters.chat_update(ChatUpdate.Status.KICKED))
        @self.five.on_update(filters.chat_update(ChatUpdate.Status.KICKED))
        

        @self.one.on_update(filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        @self.two.on_update(filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        @self.three.on_update(filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        @self.four.on_update(filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        @self.five.on_update(filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        
            
        @self.one.on_update(filters.chat_update(ChatUpdate.Status.LEFT_GROUP))
        @self.two.on_update(filters.chat_update(ChatUpdate.Status.LEFT_GROUP))
        @self.three.on_update(filters.chat_update(ChatUpdate.Status.LEFT_GROUP))
        @self.four.on_update(filters.chat_update(ChatUpdate.Status.LEFT_GROUP))
        @self.five.on_update(filters.chat_update(ChatUpdate.Status.LEFT_GROUP))
        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        @self.one.on_update()
        @self.two.on_update()
        @self.three.on_update()
        @self.four.on_update()
        @self.five.on_update()
        async def handle_update(client: PyTgCalls, update: Update):
            await self.track_vc(client, update)

        
        @self.one.on_update(filters.stream_end)
        @self.two.on_update(filters.stream_end)
        @self.three.on_update(filters.stream_end)
        @self.four.on_update(filters.stream_end)
        @self.five.on_update(filters.stream_end)
        async def stream_end_handler1(client, update: Update):
            if not isinstance(update, StreamAudioEnded):
                return
            await self.change_stream(client, update.chat_id)

BAD = Call()
