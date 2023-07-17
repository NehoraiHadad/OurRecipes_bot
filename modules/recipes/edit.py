from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

import datetime
import io

from modules.dynamoDB import RecipeHandler
from modules.s3 import delete_photo_from_s3, upload_photo_to_s3

from modules.helpers.buttons import edit_buttons, cancel_button
from modules.recipes.display import display_recipe

txt_cancel = "בטל 🛑"
txt_edit_name = "שם"
txt_edit_ingredients = "רכיבים"
txt_edit_instructions = "הוראות"
txt_edit_photo = "תמונה"
txt_edit_recipe = "עריכת מתכון"
txt_delete = "מחק"




GET_NEW_VALUE, GET_DELETE_RECIPE = range(2)


async def edit_recipe_callback(update, context):
    query = update.callback_query
    await query.answer()

    recipe_id = query.data.replace(txt_edit_recipe, "")
    await query.message.reply_text(
        text="אז מה לערוך?",
        reply_markup=InlineKeyboardMarkup(edit_buttons(update, context, recipe_id)),
    )
    message_id = query.message.message_id
    context.user_data["message_id"] = message_id


async def edit_recipe(update, context):
    query = update.callback_query
    await query.answer()
    action, recipe_id = query.data.split("_")[1:]

    context.user_data["recipe_id"] = recipe_id
    context.user_data["action"] = action

    if action == txt_edit_photo:
        await query.edit_message_text(
            f"מחכה לתמונה החדשה 🤩",
            reply_markup=InlineKeyboardMarkup([[cancel_button]]),
        )
    elif (
        action == txt_edit_ingredients
        or action == txt_edit_instructions
        or action == txt_edit_name
    ):
        await query.edit_message_text(
            f"נא להקליד את העדכון ב{action}:",
            reply_markup=InlineKeyboardMarkup([[cancel_button]]),
        )
    elif action == txt_delete:
        await query.edit_message_text(
            "בטוח שרוצה למחוק?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("כן", callback_data="OK to delete"),
                        InlineKeyboardButton("לא", callback_data=txt_cancel),
                    ]
                ]
            ),
        )

        message_id_edit = query.message.message_id
        context.user_data["message_id_edit"] = message_id_edit

        return GET_DELETE_RECIPE

    message_id_edit = query.message.message_id
    context.user_data["message_id_edit"] = message_id_edit
    return GET_NEW_VALUE


async def edit_recipe_get_respond(update, context):
    message_id = context.user_data["message_id"]
    message_id_edit = context.user_data["message_id_edit"]
    message_id_user = update.message.message_id
    await context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=message_id
    )
    await context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=message_id_edit
    )
    await context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=message_id_user
    )

    action = context.user_data["action"]
    recipe_id = context.user_data["recipe_id"]
    recipe = context.user_data[recipe_id]
    update_data = {}

    if action == txt_edit_name:
        new_name = update.message.text
        recipe["recipe_name"] = new_name
        update_data = {"recipe_name": new_name}
    elif action == txt_edit_ingredients:
        new_ingredients = update.message.text
        recipe_ingredients_list = [
            ingredient.strip() for ingredient in new_ingredients.split(",")
        ]
        recipe["ingredients"] = recipe_ingredients_list
        update_data = {"ingredients": recipe_ingredients_list
        }
    elif action == txt_edit_instructions:
        new_instructions = update.message.text
        recipe["instructions"] = new_instructions
        update_data = {"instructions": new_instructions}
    elif action == txt_edit_photo:
        new_photo_id = update.message.photo[-1].file_id
        photo = await context.bot.get_file(new_photo_id)

        # Create an in-memory file-like object to store the photo data
        photo_data = io.BytesIO()
        await photo.download_to_memory(out=photo_data)
        photo_data.seek(0)

        if recipe["photo_url"] != "":
            delete_photo_from_s3(recipe["photo_url"])
        photo_url = upload_photo_to_s3(photo_data, recipe_id)
        recipe["photo_url"] = photo_url
        update_data = {"photo_url": photo_url}

    if update_data != "":
        current_date = datetime.datetime.now()
        date_format = "%Y-%m-%d %H:%M:%S"
        date_string = current_date.strftime(date_format)
        recipe_modified = date_string

        update_data["recipe_modified"] = recipe_modified
        context.user_data[recipe["recipe_id"]]["recipe_modified"] = recipe_modified

        #  Update DB
        RecipeHandler.update_recipe(recipe_id, update_data)
        await update.message.reply_text("השינוי נשמר בהצלחה")

        await display_recipe(
            update,
            context,
            recipe,
            is_public=recipe["created_by"] != str(update.effective_user.id),
        )

    else:
        await update.message.reply_text("לא נקלט שינוי")

    keys_to_clear = ["action", "recipe_id", "message_id_edit", "message_id"]
    for key in keys_to_clear:
        del context.user_data[key]

    return ConversationHandler.END
