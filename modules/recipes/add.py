from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

import uuid
import io
import datetime

from modules.dynamoDB import RecipeHandler, UserHandler
from modules.s3 import upload_photo_to_s3

user_handler = UserHandler("users")
recipe_handler = RecipeHandler("recipes")

from modules.helpers.buttons import cancel_button, init_buttons
from modules.recipes.display import display_recipe

RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_PHOTO = range(4)


async def add_recipe_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "שם המתכון:", reply_markup=InlineKeyboardMarkup([[cancel_button]])
    )
    return RECIPE_NAME


async def get_recipe_name(update, context):
    name = update.message.text
    context.user_data["recipe_name"] = name
    await update.message.reply_text(
        "יש תמונה? (אם לא, כתוב ושלח משהו)",
        reply_markup=InlineKeyboardMarkup([[cancel_button]]),
    )
    return RECIPE_PHOTO


async def get_photo(update, context):
    if update.message.photo:
        # Photo received
        photo_id = update.message.photo[-1].file_id
        photo = await context.bot.get_file(photo_id)

        # Create an in-memory file-like object to store the photo data
        photo_data = io.BytesIO()
        await photo.download_to_memory(out=photo_data)
        photo_data.seek(0)

        context.user_data["recipe_photo"] = photo_data

        await update.message.reply_text(
            "הרכיבים (מופרדים בפסיק):",
            reply_markup=InlineKeyboardMarkup([[cancel_button]]),
        )
        return RECIPE_INGREDIENTS
    else:
        # No photo received, proceed without photo
        context.user_data["recipe_photo"] = ""

        await update.message.reply_text(
            "הרכיבים (מופרדים בפסיק):",
            reply_markup=InlineKeyboardMarkup([[cancel_button]]),
        )
        return RECIPE_INGREDIENTS


async def get_ingredients(update, context):
    ingredients = update.message.text
    context.user_data["recipe_ingredients"] = ingredients
    await update.message.reply_text(
        "הוראות:", reply_markup=InlineKeyboardMarkup([[cancel_button]])
    )
    return RECIPE_INSTRUCTIONS


async def get_instructions(update, context):
    instructions = update.message.text
    context.user_data["recipe_instructions"] = instructions
    user_id = str(update.effective_user.id)
    recipe_id = str(uuid.uuid4())

    if context.user_data["recipe_photo"] != "":
        photo_data = context.user_data["recipe_photo"]
        photo_url = upload_photo_to_s3(photo_data, recipe_id)
    else:
        photo_url = ""

    current_date = datetime.datetime.now()
    date_format = "%Y-%m-%d %H:%M:%S"
    date_string = current_date.strftime(date_format)
    recipe_created = date_string

    is_public = user_handler.is_all_public(user_id)

    recipe = {
        "recipe_id": recipe_id,
        "created_by": user_id,
        "recipe_name": context.user_data["recipe_name"],
        "ingredients": context.user_data["recipe_ingredients"],
        "instructions": context.user_data["recipe_instructions"],
        "photo_url": photo_url,
        "recipe_created": recipe_created,
        "recipe_modified": "",
        "is_public": is_public,
    }

    # Send to DynamoDB
    recipe_handler.add_recipe(
        recipe["recipe_id"],
        recipe["created_by"],
        recipe["recipe_name"],
        recipe["ingredients"],
        recipe["instructions"],
        recipe["photo_url"],
        recipe["recipe_created"],
        recipe["recipe_modified"],
        recipe["is_public"],
    )

    # Send the recipe to the user
    await display_recipe(update, context, recipe)

    context.user_data[recipe_id] = recipe
    await update.message.reply_text(
        "מה עוד?", reply_markup=InlineKeyboardMarkup(await init_buttons())
    )

    key_to_del = [
        "recipe_photo",
        "recipe_instructions",
        "recipe_ingredients",
        "recipe_name",
    ]
    for key in key_to_del:
        del context.user_data[key]

    return ConversationHandler.END
