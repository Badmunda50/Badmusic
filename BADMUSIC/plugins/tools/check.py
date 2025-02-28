from BADMUSIC import userbot as app
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pytgcalls.exceptions import InvalidMTProtoClient

try:
    vc = PyTgCalls(app)
except InvalidMTProtoClient:
    print("Invalid MTProto Client. Please check the configuration of your userbot instance.")
    raise

vc_users = {}

@vc.on_update()
async def track_vc(client: PyTgCalls, update: Update):
    global vc_users
    chat_id = update.chat_id

    participants = await vc.get_participants(chat_id)
    current_users = {p.user_id: p for p in participants}

    for user_id, user in current_users.items():
        if user_id not in vc_users:
            first_name = user.first_name if user.first_name else "Unknown"
            username = f"@{user.username}" if user.username else "No Username"
            message = f"🎙 **User Joined VC**\n👤 **Name:** {first_name}\n🔹 **Username:** {username}\n🆔 **ID:** `{user_id}`"
            await app.send_message(chat_id, message)

    for user_id in list(vc_users.keys()):
        if user_id not in current_users:
            user = vc_users[user_id]
            first_name = user.first_name if user.first_name else "Unknown"
            username = f"@{user.username}" if user.username else "No Username"
            message = f"🚫 **User Left VC**\n👤 **Name:** {first_name}\n🔹 **Username:** {username}\n🆔 **ID:** `{user_id}`"
            await app.send_message(chat_id, message)

    vc_users = current_users
