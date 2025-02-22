import asyncio
import speedtest
from pyrogram import filters
from pyrogram.types import Message

from BADMUSIC import app
from BADMUSIC.misc import SUDOERS
from BADMUSIC.utils.decorators.language import language


def testspeed(m, _):
    try:
        test = speedtest.Speedtest()
        test.get_best_server()
        m = m.edit_text("Finding the best server...")
        test.download()
        m = m.edit_text("Testing download speed...")
        test.upload()
        test.results.share()
        result = test.results.dict()
        m = m.edit_text("Sharing results...")
    except Exception as e:
        return m.edit_text(f"<code>{e}</code>")
    return result


@app.on_message(filters.command(["speedtest", "spt"]) & SUDOERS)
@language
async def speedtest_function(client, message: Message, _):
    m = await message.reply_text("Running speed test...")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, testspeed, m, _)
    output = _["server_15"].format(
        result["client"]["isp"],
        result["client"]["country"],
        result["server"]["name"],
        result["server"]["country"],
        result["server"]["cc"],
        result["server"]["sponsor"],
        result["server"]["latency"],
        result["ping"],
    )
    msg = await message.reply_photo(photo=result["share"], caption=output)
    await m.delete()
