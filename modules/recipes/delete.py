from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from modules.dynamoDB import RecipeHandler
from modules.s3 import delete_photo_from_s3

recipe_handler = RecipeHandler("recipes")

from modules.helpers.buttons import init_buttons

async def delete_recipe(update, context):
    query = update.callback_query

    message_id = context.user_data["message_id"]
    message_id_edit = context.user_data["message_id_edit"]

    recipe_id = context.user_data["recipe_id"]
    user_id = str(update.effective_user.id)
    recipe = context.user_data[recipe_id]

    # Update DB
    recipe_handler.remove_recipe(recipe_id, user_id)
    if recipe["photo_url"] != "":
        delete_photo_from_s3(recipe["photo_url"])

    await context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=message_id
    )
    await context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=message_id_edit
    )

    await query.message.reply_text("המתכון נמחק בהצלחה")
    await query.message.reply_text(
        "מה עוד?", reply_markup=InlineKeyboardMarkup(await init_buttons())
    )

    keys_to_clear = ["recipe_id", "message_id_edit", "message_id"]
    for key in keys_to_clear:
        del context.user_data[key]

    return ConversationHandler.END

