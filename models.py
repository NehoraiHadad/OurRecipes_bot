from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputTextMessageContent,
    InlineQueryResultArticle,
)

from telegram.ext import ConversationHandler
from telegram.constants import ParseMode

import uuid
import io
import datetime

from dynamoDB import RecipeHandler, UserHandler
from s3 import upload_photo_to_s3, download_photo_from_s3, delete_photo_from_s3

from utils.text_effects import add_words_bold

user_handler = UserHandler("users")
recipe_handler = RecipeHandler("recipes")


# text
txt_add_recipe = "הוסף מתכון חדש"
txt_search_recipe = "חפש מתכון"

txt_cancel = "בטל🛑"
txt_try_again = "לנסות שוב?🔄"

txt_edit_recipe = "עריכת מתכון"
txt_edit = "edit"
txt_edit_name = "שם"
txt_edit_ingredients = "רכיבים"
txt_edit_instructions = "הוראות"
txt_edit_photo = "תמונה"
txt_delete_recipe = "מחק מתכון⁉"
txt_delete = "מחק"
txt_more_details = "פרטים נוספים"

# state for conv handler
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_PHOTO = range(4)
USER_QUERY, TRY_AGAIN = range(2)
GET_NEW_VALUE, GET_DELETE_RECIPE = range(2)

# buttons
cancel_button = InlineKeyboardButton(txt_cancel, callback_data=txt_cancel)
init_buttons = [
    [InlineKeyboardButton(txt_add_recipe, callback_data=txt_add_recipe)],
    [InlineKeyboardButton(txt_search_recipe, callback_data=txt_search_recipe)],
]


async def edit_buttons(recipe_id):
    return (
        [
            InlineKeyboardButton(
                txt_edit_name, callback_data=f"{txt_edit}_{txt_edit_name}_{recipe_id}"
            ),
            InlineKeyboardButton(
                txt_edit_ingredients,
                callback_data=f"{txt_edit}_{txt_edit_ingredients}_{recipe_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                txt_edit_instructions,
                callback_data=f"{txt_edit}_{txt_edit_instructions}_{recipe_id}",
            ),
            InlineKeyboardButton(
                txt_edit_photo, callback_data=f"{txt_edit}_{txt_edit_photo}_{recipe_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                txt_delete_recipe, callback_data=f"{txt_edit}_{txt_delete}_{recipe_id}"
            ),
            cancel_button,
        ],
    )


def edit_recipe_button(recipe_id):
    return InlineKeyboardButton(
        txt_edit_recipe, callback_data=f"{txt_edit_recipe}{recipe_id}"
    )


def more_details_button(recipe_id):
    return InlineKeyboardButton(
        txt_more_details, callback_data=f"{txt_more_details}{recipe_id}"
    )


# commends
async def start(update, context):
    user_id = str(update.message.from_user.id)
    username = update.effective_user.first_name
    context.user_data["user_id"] = user_id
    context.user_data["user_name"] = username
    response = user_handler.register_user(user_id, username, [])

    if response:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"שלום {username}!\nאני בוט מתכונים! בו ניתן להוסיף לערוך ולחפש את המתכונים בצורה נוחה...",
            reply_markup=InlineKeyboardMarkup(init_buttons),
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="יש לנו בעיה... יש ללחוץ שוב על /start"
        )


async def unknown(update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="לא מכיר את הפקודה הזו  ):"
    )


# display functions
async def display_recipe(update, context, recipe):
    context.user_data[recipe["recipe_id"]] = recipe

    recipe_ingredients_list = [
        ingredient.strip() for ingredient in recipe["ingredients"].split(",")
    ]
    formatted_ingredients = "\n".join(
        [
            f"{index+1}\.  {ingredient}"
            for index, ingredient in enumerate(recipe_ingredients_list)
        ]
    )

    recipe_str = f'*שם:*  {recipe["recipe_name"]}\n\n*רכיבים:*\n{formatted_ingredients}\n\n*הוראות:*\n{recipe["instructions"]}'

    if recipe["photo_url"] != None:
        photo = download_photo_from_s3(recipe["photo_url"])
        await photo_display_recipe(
            update, context, photo, recipe["recipe_id"], recipe_str
        )
    else:
        await txt_display_recipe(update, context, recipe["recipe_id"], recipe_str)


async def photo_display_recipe(update, context, photo, recipe_id, recipe_str):
    reply_markup = InlineKeyboardMarkup(
        [[edit_recipe_button(recipe_id), more_details_button(recipe_id)]]
    )
    await context.bot.send_photo(
        update.effective_chat.id,
        photo=photo,
        caption=recipe_str,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup,
    )


async def txt_display_recipe(update, context, recipe_id, recipe_str):
    reply_markup = InlineKeyboardMarkup(
        [[edit_recipe_button(recipe_id), more_details_button(recipe_id)]]
    )
    await update.message.reply_text(
        recipe_str,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup,
    )


# add recipe


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
    user_id = context.user_data["user_id"]
    photo_data = context.user_data["recipe_photo"]

    recipe_id = str(uuid.uuid4())
    photo_url = await upload_photo_to_s3(photo_data, recipe_id)

    current_date = datetime.datetime.now()
    date_format = '%Y-%m-%d %H:%M:%S'
    date_string = current_date.strftime(date_format)
    recipe_created = date_string

    recipe = {
        "recipe_id": recipe_id,
        "created_by": user_id,
        "recipe_name": context.user_data["recipe_name"],
        "ingredients": context.user_data["recipe_ingredients"],
        "instructions": context.user_data["recipe_instructions"],
        "photo_url": photo_url,
        "recipe_created": recipe_created,
        "recipe_modified": "",
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
    )

    # TO DO - In display_recipe function: change (just here) the recipe param to inclode the photo from user not from DB
    # Send the recipe to the user
    await display_recipe(update, context, recipe)

    context.user_data[recipe_id] = recipe
    await update.message.reply_text(
        "מה עוד?", reply_markup=InlineKeyboardMarkup(init_buttons)
    )
    return ConversationHandler.END


async def cancel(update, context):
    await update.callback_query.edit_message_text("הפעולה בוטלה.")
    await update.callback_query.message.reply_text(
        "מה עוד?", reply_markup=InlineKeyboardMarkup(init_buttons)
    )

    # context.user_data.clear()  -- I need to use pop instead clear method
    return ConversationHandler.END


# search recipe
async def search_recipe_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "מה לחפש?", reply_markup=InlineKeyboardMarkup([[cancel_button]])
    )
    return USER_QUERY


async def get_user_search(update, context):
    user_query = update.message.text
    context.user_data["user_query"] = user_query
    user_id = context.user_data["user_id"]

    # Perform the search and retrieve matching recipes from DB
    accessible_recipes = user_handler.get_accessible_recipes(user_id)
    matching_recipes = recipe_handler.search_recipes_by_name(
        accessible_recipes, user_query
    )

    # Send the search results to the user
    if matching_recipes:
        for recipe in matching_recipes:
            await display_recipe(update, context, recipe)
    else:
        await update.message.reply_text(
            "לא מצאתי מתכון מתאים 😕",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        cancel_button,
                        InlineKeyboardButton(
                            txt_try_again, callback_data=txt_try_again
                        ),
                    ]
                ]
            ),
        )
        return TRY_AGAIN

    return ConversationHandler.END


# edit recipe
async def edit_recipe_callback(update, context):
    query = update.callback_query
    await query.answer()

    recipe_id = query.data.replace(txt_edit_recipe, "")
    await query.message.reply_text(
        text="אז מה לערוך?",
        reply_markup=InlineKeyboardMarkup(await edit_buttons(recipe_id)),
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
            f"מחכה לשליחת תמונה חדשה",
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
        recipe["ingredients"] = new_ingredients
        update_data = {"ingredients": new_ingredients}
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

        photo_url = await upload_photo_to_s3(photo_data, recipe_id)
        if recipe["photo_url"] != "":
            delete_photo_from_s3(recipe["photo_url"])

        recipe["photo_url"] = photo_url
        update_data = {"photo_url": photo_url}

    if update_data != "":
        current_date = datetime.datetime.now()
        date_format = '%Y-%m-%d %H:%M:%S'
        date_string = current_date.strftime(date_format)
        recipe_modified = date_string

        update_data["recipe_modified"] = recipe_modified
 
        #  Update DB
        recipe_handler.update_recipe(recipe_id, update_data)
        await update.message.reply_text("השינוי נשמר בהצלחה")

        # TO DO - In display_recipe function: change (just here) the recipe param to inclode the photo from user not from DB
        await display_recipe(update, context, recipe)

    else:
        await update.message.reply_text('לא נקלט שינוי')

    keys_to_clear = ["action", "recipe_id", "message_id_edit", "message_id"]
    for key in keys_to_clear:
        if key in context.user_data:
            del context.user_data[key]


    return ConversationHandler.END


async def delete_recipe(update, context):
    query = update.callback_query

    message_id = context.user_data["message_id"]
    message_id_edit = context.user_data["message_id_edit"]

    recipe_id = context.user_data["recipe_id"]
    user_id = context.user_data["user_id"]
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
        "מה עוד?", reply_markup=InlineKeyboardMarkup(init_buttons)
    )

    return ConversationHandler.END


async def more_details(update, context):
    query = update.callback_query
    await query.answer()
    
    recipe_id = query.data.replace(txt_more_details, "")
    recipe = context.user_data[recipe_id]

    bold_words = ['שם:', 'רכיבים:', 'הוראות:']

    date_format = '%Y-%m-%d %H:%M:%S'

    if recipe["recipe_modified"] != '':
        str_modified =  recipe["recipe_modified"] 
        str_modified = datetime.datetime.strptime(str_modified, date_format)
    else:
        str_modified = "המתכון לא עבר שינוי"

    created_by = datetime.datetime.strptime(recipe["recipe_created"], date_format)
    more_details_str = f"\n\n*תאריך הוספה:*  {created_by}\n\n*תאריך שינוי:*  {str_modified}"

    if query.message.photo:
        caption_bold = add_words_bold(query.message.caption, bold_words)
        await query.message.edit_caption(
            caption=f"{caption_bold}{more_details_str}",
            reply_markup=InlineKeyboardMarkup([[edit_recipe_button(recipe_id)]]),
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        text_bold = add_words_bold(query.message.text, bold_words)
        await query.message.edit_text(
            text=f"{text_bold}{more_details_str}",
            reply_markup=InlineKeyboardMarkup([[edit_recipe_button(recipe_id)]]),
            parse_mode=ParseMode.MARKDOWN,
        )


# inline mode
async def inline_query(update, context):
    query = update.inline_query.query
    user_id = str(update.inline_query.from_user.id)

    # Retrieve matching recipes from database
    accessible_recipes = user_handler.get_accessible_recipes(user_id)
    matching_recipes = recipe_handler.search_recipes_by_name(accessible_recipes, query)

    # inline query results
    results = []
    for recipe in matching_recipes:
        recipe_str = f'*שם:*  {recipe["recipe_name"]}\n\n*רכיבים:*  {recipe["ingredients"]}\n\n*הוראות:*  {recipe["instructions"]}'

        result = InlineQueryResultArticle(
            id=recipe["recipe_id"],
            title=recipe["recipe_name"],
            input_message_content=InputTextMessageContent(
                message_text=recipe_str, parse_mode="Markdown"
            ),
            thumb_url="https://picsum.photos/200/300",
        )
        results.append(result)

    await context.bot.answer_inline_query(update.inline_query.id, results)
