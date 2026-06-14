import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import BaseFilter, Command
from aiogram.exceptions import TelegramAPIError
from detector import SpamDetector 
import db

import os
from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
detector = SpamDetector()

class IsGroupMessage(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in ["group", "supergroup"]
    
@dp.message(IsGroupMessage(), Command("spam"))
async def admin_mark_spam(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("команду нужно писать в ответ на спам-сообщение")
        return

    try:
        member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
        if member.status not in ["creator", "administrator"]:
            return 
    except TelegramAPIError as e:
        logging.error(f"не удалось проверить права{e}")
        return

    spam_msg = message.reply_to_message
    spam_text = spam_msg.text or spam_msg.caption 

    if spam_text:
        spammer_id = spam_msg.from_user.id if spam_msg.from_user else 0
        
        await asyncio.to_thread(db.save_missed_spam, user_id=spammer_id, text=spam_text)
        logging.info(f"сообщение записано в БД: {spam_text[:50]}")

        try:
            await spam_msg.delete()
        except TelegramAPIError as e:
            logging.error(f"не удалось удалить сообщение спамера: {e}")
            
        try:
            await message.delete()
        except TelegramAPIError as e:
            logging.error(f"не удалось удалить команду /spam: {e}")
            
@dp.message(IsGroupMessage())
async def handle_group_message(message: types.Message):

    #print(f"ID этого чата: {message.chat.id}")
    
    if message.text and message.text.startswith('/'):
        return

    text_to_check = message.text or message.caption
    if not text_to_check:
        return

    logging.info(f"на проверке сообщение от {message.from_user.full_name if message.from_user else 'канала'}")
    
    user_id = message.from_user.id if message.from_user else "Channel/Anonymous"

    is_spam = await detector.is_spam_async(text_to_check)

    if is_spam:
        try:
            await message.delete()
            logging.info(f"был удален спам от {user_id}: {text_to_check[:60]}...")
        except TelegramAPIError as e:
            logging.error(f"не удалось удалить сообщение: {e}")

async def main():
    await asyncio.to_thread(db.init_db)
    
    print("бот запущен")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())