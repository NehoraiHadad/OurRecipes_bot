from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from modules.helpers.buttons import init_buttons


async def cancel(update, context):
    await update.callback_query.edit_message_text("הפעולה בוטלה.")
    await update.callback_query.message.reply_text(
        "מה עוד?", reply_markup=InlineKeyboardMarkup(await init_buttons())
    )

    # TO DO - context.user_data.clear()  -- I need to use pop instead clear method
    return ConversationHandler.END
