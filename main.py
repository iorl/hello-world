import logging
import asyncio
import configparser
from tinydb import TinyDB, Query
from pyrogram import Client, emoji, idle, filters
from pyrogram.types import Message


# logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger(__name__)


# Configurations
config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config.get('bot-configuration', 'bot_token')
SESSION = config.get('bot-configuration', 'bot_session')
GROUP = int(config.get('bot-configuration', 'group'))
DEV = int(config.get('users', 'dev'))
OWNER = int(config.get('users', 'owner'))


# Database
blocked_users = TinyDB('blocked_user.json')
all_users = TinyDB('users.json')
q = Query()


# bot connection credentials
bot = Client(
    session_name=SESSION,
    bot_token=TOKEN,
    workers=50
)


async def main():
    await bot.start()
    await idle()


@bot.on_message(filters=filters.private & filters.command(commands='start', prefixes='/'))
async def start_command_handler(_, m: Message):
    # Adding users to the database if they aren't already added.
    if not all_users.search(q.user_id == m.from_user.id):
        all_users.insert({'user_name': m.from_user.first_name, 'user_id': m.from_user.id})

    # Checking if user is blocked or not.
    if not blocked_users.search(q.user_id == m.from_user.id):
        await m.reply('Use this bot to send links to offending groups to Report Child Abuse (@ReportCA).'
                      ' Please begin your message with #report')


@bot.on_message(filters.command('id'))
async def return_id(_, m: Message):
    if blocked_users.search(q.user_id == m.from_user.id):
        return

    await m.reply_text(
        text=f"{m.from_user.id}"
    )


@bot.on_message(filters.command(commands=['report', 'Report'], prefixes=['/', '#']))
async def new_report_handler(_, m: Message):
    # if user is blocked.
    if blocked_users.search(q.user_id == m.from_user.id):
        return

    if len(m.command) > 1:
        fwd = await m.copy(GROUP)
        await fwd.edit_text(
            text=f"{emoji.WARNING} {m.from_user.mention} Reported :\n{m.text.replace('#report', '')}"
        )
        await m.reply(f'{emoji.FOLDED_HANDS} Thank you for your report. Rest assured that your report is helping to'
                      f' reduce the pain, '
                      f'suffering and fear of children and young teens who are being exploited on Telegram. If you '
                      f'require a response, need assistance or would like to help, please send a message to '
                      f'@ReportCA_DM.')

    else:
        await m.reply_text(
            text=f"{emoji.CROSS_MARK} Sorry u need to report something."
        )


# Block users
@bot.on_message(filters.reply & filters.command('block') & filters.group)
async def block_user_handler(_, m: Message):
    admins = await admin_list(m)
    if m.from_user.id in admins:
        try:
            if m.reply_to_message.entities[0].type == 'text_mention':
                blocked_users.insert({'user_id': m.reply_to_message.entities[0].user.id})
                await m.reply_text(
                    text=f"{emoji.PROHIBITED} {m.reply_to_message.entities[0].user.mention} has been Blocked."
                         f" He cannot use me anymore!"
                )
            else:
                await m.reply_text(
                    text=f"Please only reply to reports message.\n"
                         f"if user does not have link to their profile, then I can't block him. "
                         f"If user does then please report this error to <a href='tg://user?id='{DEV}'>xeact</a>"

                )
        except Exception as e:
            logging.error(e)
            await m.reply_text(
                text=f"Something went wrong!!! report this to <a href='tg://user?id={DEV}'>xeact</a>\nerror:\n{e}"
            )
    else:
        await m.reply_text(text=f"{emoji.PROHIBITED} You need to be an admin to use this command.")


# unblock user
@bot.on_message(filters.command('unblock') & filters.group)
async def unblock_user_handler(_, m: Message):
    if len(m.command) == 2:
        admins = await admin_list(m)

        if len(m.command) == 2 and m.from_user.id in admins:
            try:
                blocked_users.remove(q.user_id == int(m.command[1]))
                await m.reply(
                    text=f"{emoji.PERSON} User has been unblocked."
                )
            except Exception as e:
                logging.error(e)
                await m.reply(
                    text=f"Something went wrong!!! <a href='tg://user?id={DEV}>xeact</a>\nerror:\n{e}"
                )
        else:
            await m.reply_text(
                text=f"{emoji.PROHIBITED} You need admins right to use this command."
            )

    else:
        await m.reply_text(
            text=f"<code>/unblock 3420131 </code> use this format to unblock user."
        )


@bot.on_message(filters.command('blocklist') & filters.group)
async def blocklist_command_handler(c: Client, m: Message):
    admins = await admin_list(m)
    if len(m.command) == 1 and m.from_user.id in admins:
        if blocked_users.all():
            block_list = ""
            # users = [user[0] for user in blocked_users.all()]
            # try:
            #     await c.get_users(users)
            for num, each in enumerate(blocked_users.all()):
                try:
                    user = await c.get_users(each['user_id'])
                    block_list += f"{num + 1} {emoji.BUST_IN_SILHOUETTE} {user.first_name} <code>{each['user_id']}" \
                                  f"</code>\n"
                except Exception as e:
                    logging.error(e)
                    block_list += f"{num + 1} {emoji.BUST_IN_SILHOUETTE} Deleted <code>{each['user_id']}</code>\n"

            await m.reply_text(
                text=block_list
            )
        else:
            await m.reply_text(f"{emoji.SPARKLES} NO ONE IS BLOCKED.")


async def admin_list(m: Message):
    admin_obj = await bot.get_chat_members(m.chat.id, filter='administrators')
    return [
        admin.user.id for admin
        in admin_obj
    ]

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
