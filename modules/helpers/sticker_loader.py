import random


async def start_sticker_loader(update, context):
    stickers = [
        'CAACAgIAAxkBAAIHWmSwczoyZPfw1tBzEFDdiN8MgIR9AAJvAAPBnGAMyw59i8DdTVYvBA',
        'CAACAgIAAxkBAAIHW2Swc-2FJjSK3j-mO5sBtQWM0DY9AAIeAAPANk8ToWBbLasAAd4ELwQ',
        'CAACAgIAAxkBAAIHXGSwdDrBvjmYr94U6B45af4kU6t1AAInAAOQ_ZoVbZYCG6YB3WEvBA'
    ]

    # start loader
    chosen_sticker = random.choice(stickers)
    stiker_message = await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=chosen_sticker)

    return stiker_message

async def stop_sticker_loader(update, context, stiker_message):
    # close loader
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=stiker_message.message_id)
