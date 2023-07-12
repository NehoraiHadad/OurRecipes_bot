from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputTextMessageContent,
    InlineQueryResultArticle,
)

from telegram.ext import ConversationHandler
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

import uuid
import io
import datetime

from dynamoDB import RecipeHandler, UserHandler, SharesHandler
from s3 import upload_photo_to_s3, download_photo_from_s3, delete_photo_from_s3

from utils.text_effects import add_words_bold

user_handler = UserHandler("users")
recipe_handler = RecipeHandler("recipes")
shares_handler = SharesHandler("shares")


# text
txt_add_recipe = "הוסף מתכון חדש"
txt_search_recipe = "חפש מתכון"

txt_cancel = "בטל 🛑"
txt_try_again = "לנסות שוב? 🔄"

txt_edit_recipe = "עריכת מתכון"
txt_edit = "edit"
txt_edit_name = "שם"
txt_edit_ingredients = "רכיבים"
txt_edit_instructions = "הוראות"
txt_edit_photo = "תמונה"
txt_delete_recipe = "מחק מתכון⁉"
txt_delete = "מחק"
txt_more_details = "פרטים נוספים"
txt_share_recipe = "שיתוף"
txt_share_button_start_en = "b-start"
txt_share_button_public_en = "b-public"
txt_share_button_link_en = "b-link"
txt_share_button_togglt_public_en = "b-togglt_public"
txt_share_button_create_link_en = "b-create-link"
txt_share_button_revoke_or_not = "b-revoke-or-not"
txt_share_button_revoke = "revoke"
txt_share_button_save = "save"
txt_share_single = "share-single"
txt_share_all = "share-all"
txt_share_link = "יצירת לינק"
txt_share_link_en = "link"
txt_share_public = "ציבורי/פרטי"
txt_share_public_en = "public"
txt_share_edit = "עריכה"
txt_share_edit_en = "edit"
txt_share_view = "צפייה"
txt_share_view_en = "view"

# state for conv handler
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_PHOTO = range(4)
USER_QUERY, TRY_AGAIN = range(2)
GET_NEW_VALUE, GET_DELETE_RECIPE = range(2)

# buttons
cancel_button = InlineKeyboardButton(txt_cancel, callback_data=txt_cancel)


async def init_buttons():
    init_buttons = [
        [InlineKeyboardButton(txt_add_recipe, callback_data=txt_add_recipe)],
        [InlineKeyboardButton(txt_search_recipe, callback_data=txt_search_recipe)],
        [await share_button(is_all_or_single=txt_share_all)],
    ]
    return init_buttons


def edit_buttons(context, recipe_id):
    recipe = context.user_data[recipe_id]
    if recipe["created_by"] == context.user_data["user_id"]:
        bottons = (
            [
                InlineKeyboardButton(
                    txt_edit_name,
                    callback_data=f"{txt_edit}_{txt_edit_name}_{recipe_id}",
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
                    txt_edit_photo,
                    callback_data=f"{txt_edit}_{txt_edit_photo}_{recipe_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    txt_delete_recipe,
                    callback_data=f"{txt_edit}_{txt_delete}_{recipe_id}",
                ),
                cancel_button,
            ],
        )
    else:
        bottons = (
            [
                InlineKeyboardButton(
                    txt_edit_name,
                    callback_data=f"{txt_edit}_{txt_edit_name}_{recipe_id}",
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
                    txt_edit_photo,
                    callback_data=f"{txt_edit}_{txt_edit_photo}_{recipe_id}",
                ),
            ],
            [cancel_button],
        )
    return bottons


async def edit_recipe_button(recipe_id):
    return InlineKeyboardButton(
        txt_edit_recipe, callback_data=f"{txt_edit_recipe}{recipe_id}"
    )


async def more_details_button(recipe_id):
    return InlineKeyboardButton(
        txt_more_details, callback_data=f"{txt_more_details}{recipe_id}"
    )


async def share_button(is_all_or_single, recipe_id=None):
    return InlineKeyboardButton(
        txt_share_recipe,
        callback_data=txt_share_button_start_en
        + "_"
        + is_all_or_single
        + ("_" + recipe_id if recipe_id is not None else ""),
    )


def share_buttons_link_or_public(unique_id):
    return [
        InlineKeyboardButton(
            txt_share_link,
            callback_data=txt_share_button_link_en
            + "_"
            + unique_id
            + "_"
            + txt_share_link_en,
        ),
        InlineKeyboardButton(
            txt_share_public,
            callback_data=txt_share_button_public_en
            + "_"
            + unique_id
            + "_"
            + txt_share_public_en,
        ),
    ]


def share_buttons_public_or_privet(is_public):
    return [
        InlineKeyboardButton(
            "הפוך לפרטי" if is_public else "הפוך לציבורי",
            callback_data=txt_share_button_togglt_public_en,
        ),
    ]


def share_buttons_permissions(unique_id):
    return [
        InlineKeyboardButton(
            txt_share_edit,
            callback_data=txt_share_button_create_link_en
            + "_"
            + unique_id
            + "_"
            + txt_share_edit_en,
        ),
        InlineKeyboardButton(
            txt_share_view,
            callback_data=txt_share_button_create_link_en
            + "_"
            + unique_id
            + "_"
            + txt_share_view_en,
        ),
    ]


def share_buttons_revoke_or_not():
    return [
        InlineKeyboardButton(
            "לבטל",
            callback_data=txt_share_button_revoke_or_not
            + "_"
            + txt_share_button_revoke,
        ),
        InlineKeyboardButton(
            "לשמור",
            callback_data=txt_share_button_revoke_or_not + "_" + txt_share_button_save,
        ),
    ]


# commends
async def start(update, context):
    user_id = str(update.message.from_user.id)
    username = update.effective_user.first_name
    context.user_data["user_id"] = user_id
    context.user_data["user_name"] = username
    unique_id = None

    if context.args:
        unique_id = context.args[0]
        share_info = shares_handler.fetch_share_info(unique_id)
        if share_info["user_id"] == user_id:
            await update.message.reply_text("אין אפשרות לשתף מתכון עם עצמך :)")
            unique_id = None
        elif share_info["link_status"] == "cancelled":
            await update.message.reply_text("השתמשת בלינק ישן\. תמיד אפשר לבקש חדש 😎")
            unique_id = None
        elif share_info["recipe_id"] or share_info["all_recipes"]:
            shares_handler.add_share_access(unique_id, user_id)
            await update.message.reply_text(
                "שותפת עם מתכון!"
                if share_info["recipe_id"]
                else "שותפת עם מלא מתכונים!"
            )

    response = user_handler.register_user(
        user_id, username, shared_recipes=unique_id if unique_id else None
    )

    if response:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"שלום {username}!\nאני בוט מתכונים! בו ניתן להוסיף לערוך ולחפש את המתכונים בצורה נוחה...",
            reply_markup=InlineKeyboardMarkup(await init_buttons()),
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="יש לנו בעיה... יש ללחוץ שוב על /start",
        )


async def unknown(update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="לא מכיר את הפקודה הזו  ):"
    )


# display functions
async def display_recipe(update, context, recipe, is_shared=False, is_public=False):
    context.user_data[recipe["recipe_id"]] = recipe

    if type(recipe["ingredients"]) != list:
        recipe["ingredients"] = [
            ingredient.strip() for ingredient in recipe["ingredients"].split(",")
        ]

    formatted_ingredients = "\n".join(
        [
            f"{index+1}.  {ingredient}"
            for index, ingredient in enumerate(recipe["ingredients"])
        ]
    )
    recipe_str = f'*שם:*  {escape_markdown(recipe["recipe_name"], 2)}\n\n*רכיבים:*\n{escape_markdown(formatted_ingredients, 2)}\n\n*הוראות:*\n{escape_markdown(recipe["instructions"], 2)}'

    message = None
    if recipe["photo_url"]:
        photo = download_photo_from_s3(recipe["photo_url"])
        message = await context.bot.send_photo(
            update.effective_chat.id,
            photo=photo,
            caption=recipe_str,
            parse_mode=ParseMode.MARKDOWN_V2,
            # TO DO - fix the reply_markup for owner and public
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        await edit_recipe_button(recipe["recipe_id"]),
                        await more_details_button(recipe["recipe_id"]),
                    ],
                    [
                        await share_button(
                            is_all_or_single=txt_share_single,
                            recipe_id=recipe["recipe_id"],
                        )
                    ],
                ],
            )
            if not is_shared and not is_public
            else None,
        )
    else:
        message = await update.message.reply_text(
            recipe_str,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        await edit_recipe_button(recipe["recipe_id"]),
                        await more_details_button(recipe["recipe_id"]),
                    ],
                    [
                        await share_button(
                            is_all_or_single=txt_share_single,
                            recipe_id=recipe["recipe_id"],
                        )
                    ],
                ],
            )
            if not is_shared and not is_public
            else None,
        )

    if is_shared:
        await update_message_with_permissions(context, message, recipe["recipe_id"])


async def update_message_with_permissions(context, message, recipe_id):
    shared_recipe_permission = context.user_data["shared_recipe_permissions"].get(
        recipe_id
    )
    if shared_recipe_permission == "edit":
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    await edit_recipe_button(recipe_id),
                    await more_details_button(recipe_id),
                ]
            ]
        )

        await context.bot.edit_message_reply_markup(
            chat_id=message.chat_id,
            message_id=message.message_id,
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

    # TO DO - In display_recipe function: change (just here) the recipe param to inclode the photo from user not from DB
    # Send the recipe to the user
    await display_recipe(update, context, recipe)

    context.user_data[recipe_id] = recipe
    await update.message.reply_text(
        "מה עוד?", reply_markup=InlineKeyboardMarkup(await init_buttons())
    )
    return ConversationHandler.END


async def cancel(update, context):
    await update.callback_query.edit_message_text("הפעולה בוטלה.")
    await update.callback_query.message.reply_text(
        "מה עוד?", reply_markup=InlineKeyboardMarkup(await init_buttons())
    )

    # TO DO - context.user_data.clear()  -- I need to use pop instead clear method
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

    # Perform the search and retrieve matching recipes from DB
    owned_recipes, shared_recipes, public_recipes = await update_accessable_recipes(
        update, context
    )

    matching_recipes_owned = recipe_handler.search_recipes_by_name(
        owned_recipes, user_query
    )
    matching_recipes_shared = recipe_handler.search_recipes_by_name(
        shared_recipes, user_query
    )
    matching_recipes_publicd = local_search_recipes_by_name(public_recipes, user_query)

    # Send the search results to the user
    if matching_recipes_owned or matching_recipes_shared or matching_recipes_publicd:
        if matching_recipes_owned:
            for recipe in matching_recipes_owned:
                await display_recipe(update, context, recipe)
        if matching_recipes_shared:
            for recipe in matching_recipes_shared:
                await display_recipe(update, context, recipe, is_shared=True)
        if matching_recipes_publicd:
            for recipe in matching_recipes_publicd:
                await display_recipe(update, context, recipe, is_public=True)
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


def local_search_recipes_by_name(recipes, user_query):
    matching_recipes = []
    for recipe in recipes:
        if user_query in recipe["recipe_name"]:
            matching_recipes.append(recipe)
    return matching_recipes


# edit recipe
async def edit_recipe_callback(update, context):
    query = update.callback_query
    await query.answer()

    recipe_id = query.data.replace(txt_edit_recipe, "")
    await query.message.reply_text(
        text="אז מה לערוך?",
        reply_markup=InlineKeyboardMarkup(edit_buttons(context, recipe_id)),
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
        recipe_handler.update_recipe(recipe_id, update_data)
        await update.message.reply_text("השינוי נשמר בהצלחה")

        # TO DO - In display_recipe function: change (just here) the recipe param to inclode the photo from user not from DB
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
        "מה עוד?", reply_markup=InlineKeyboardMarkup(await init_buttons())
    )

    return ConversationHandler.END


async def more_details(update, context):
    query = update.callback_query
    await query.answer()

    recipe_id = query.data.replace(txt_more_details, "")
    recipe = context.user_data[recipe_id]

    bold_words = ["שם:", "רכיבים:", "הוראות:"]

    date_format = "%Y-%m-%d %H:%M:%S"

    if recipe["recipe_modified"] != "":
        str_modified = recipe["recipe_modified"]
        str_modified = escape_markdown(
            str(datetime.datetime.strptime(str_modified, date_format)), 2
        )
    else:
        str_modified = "המתכון לא עבר שינוי"

    created_by = escape_markdown(
        str(datetime.datetime.strptime(recipe["recipe_created"], date_format)), 2
    )
    more_details_str = (
        f"\n\n*תאריך הוספה:*  {created_by}\n\n*תאריך שינוי:*  {str_modified}"
    )

    if query.message.photo:
        caption_bold = add_words_bold(query.message.caption, bold_words)
        await query.message.edit_caption(
            caption=f"{caption_bold}{more_details_str}",
            reply_markup=InlineKeyboardMarkup([[await edit_recipe_button(recipe_id)]]),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        text_bold = add_words_bold(query.message.text, bold_words)
        await query.message.edit_text(
            text=f"{text_bold}{more_details_str}",
            reply_markup=InlineKeyboardMarkup([[await edit_recipe_button(recipe_id)]]),
            parse_mode=ParseMode.MARKDOWN_V2,
        )


async def generate_text_for_share(
    context, active_sharing_infos, is_public, all_recipes, recipe_id=None
):
    text_public = (
        "\- " + "כל המתכונים שלך *ציבוריים*\.\n"
        if is_public
        else "כל המתכונים שלך *פרטיים*\.\n"
    )
    if not all_recipes:
        text_public = "\- " + (
            "המתכון שלך *ציבורי*\.\n\n" if is_public else "המתכון שלך *פרטי*\.\n"
        )

    if active_sharing_infos:
        text_links = ""
        for active_sharing_info in active_sharing_infos:
            if (all_recipes and active_sharing_info["all_recipes"]) or (
                not all_recipes and active_sharing_info["recipe_id"] == recipe_id
            ):
                permission_level = (
                    "צפייה"
                    if active_sharing_info["permission_level"] == "view"
                    else "עריכה"
                )
                share_link = f"`https://t.me/{context.bot.username}?start={active_sharing_info['unique_id']}`"
                text_link = f"\- לינק פעיל:\n{share_link}\nברמת הרשאות: *{permission_level}*\n\n"
                text_links += text_link
                if "links_share_revoke" in context.user_data:
                    context.user_data["links_share_revoke"][
                        active_sharing_info["permission_level"]
                    ] = active_sharing_info
                else:
                    context.user_data["links_share_revoke"] = {}
                    context.user_data["links_share_revoke"][
                        active_sharing_info["permission_level"]
                    ] = active_sharing_info
        if text_links:
            return (
                text_public
                + text_links
                + "ניתן להשתמש בקישור או לבטל אותו על ידי יצירת חלופי\.\nבכל מקרה לא יתכנו שני קישורים פעילים באותה רמת הרשאות\."
            )
    return text_public + "\- לא קיימים לינקים פעילים\."


async def share_callback(update, context):
    query = update.callback_query
    await query.answer()

    unique_id = str(uuid.uuid4())
    user_id = str(update.effective_user.id)
    user_shared_ids = user_handler.get_user_shares(user_id)
    text = "ברוכים הבאים לתפריט השיתוף\!\n\nהמצב פה כרגע:\n"

    query_data = query.data.split("_")

    # all recipes or single recipe
    is_all_or_single = query_data[1]

    if "share" not in context.user_data:
        context.user_data["share"] = {}

    current_date = datetime.datetime.now()
    date_format = "%Y-%m-%d %H:%M:%S"
    date_string = current_date.strftime(date_format)

    new_sharing_info = {
        "unique_id": unique_id,
        "user_id": user_id,
        "all_recipes": False,
        "recipe_id": "",
        "link_or_public": "",
        "permission_level": "view",
        "link_status": "active",
        "link_created": date_string,
    }

    if is_all_or_single == txt_share_all:
        new_sharing_info["all_recipes"] = True
        is_public = user_handler.is_all_public(user_id)
        text += await generate_text_for_share(
            context, user_shared_ids, is_public, all_recipes=True
        )
        context.user_data["share"]["public"] = {
            "is_public": is_public,
            "all_recipes": True,
        }

    else:
        recipe_id = query_data[2]
        new_sharing_info["recipe_id"] = recipe_id
        is_public = recipe_handler.is_recipe_public(recipe_id)
        text += await generate_text_for_share(
            context,
            user_shared_ids,
            is_public,
            all_recipes=False,
            recipe_id=recipe_id,
        )
        context.user_data["share"]["public"] = {
            "is_public": is_public,
            "all_recipes": False,
            "recipe_id": recipe_id,
        }

    context.user_data["share"][unique_id] = new_sharing_info

    return await query.message.reply_text(
        text
        + "\n\n"
        + "איך לשתף?\n\n*אפשרות* אחת לשתף לכולם על ידי הפיכה לציבורי\.\nאפשרות *אחרת* לשתף בעזרת קישור שניתן לשלוח למי שרוצים לשתף\.",
        reply_markup=InlineKeyboardMarkup(
            [share_buttons_link_or_public(unique_id), [cancel_button]]
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def share_public_state(update, context):
    query = update.callback_query
    await query.answer()

    is_public = context.user_data["share"]["public"]["is_public"]
    state = "ציבורי" if not is_public else "פרטי"

    text = f"בטוח שתרצה להפוך ל{state}?"

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [share_buttons_public_or_privet(is_public), [cancel_button]]
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def share_togglt_public(update, context):
    query = update.callback_query

    public_info = context.user_data["share"]["public"]
    user_id = str(update.effective_user.id)

    if public_info["all_recipes"]:
        if public_info["is_public"]:
            recipe_handler.revoke_all_public(user_id)
            user_handler.update_all_recipes_public(user_id, False)
            text = "המתכונים שלך פרטיים עכשיו"
        else:
            recipe_handler.make_all_public(user_id)
            user_handler.update_all_recipes_public(user_id, True)
            text = "כל המתכונים שלך ציבוריים עכשיו!\n נחמד מצידך 🙂"

        await query.edit_message_text(text)

    else:
        if public_info["is_public"]:
            recipe_handler.revoke_public(public_info["recipe_id"])
            text = "המתכון שלך פרטי עכשיו"
        else:
            recipe_handler.make_public(public_info["recipe_id"])
            text = "המתכון שלך ציבורי עכשיו!\n נחמד מצידך 🙂"

        await query.edit_message_text(text)

    if "public" in context.user_data["share"]:
        del context.user_data["share"]["public"]


async def share_permission_level(update, context):
    query = update.callback_query
    await query.answer()

    query_data = query.data.split("_")
    unique_id = query_data[1]
    link_or_public = query_data[2]

    if link_or_public == txt_share_link_en:
        link = link_or_public
        context.user_data["share"][unique_id]["link_or_public"] = link
        text = "הכי טוב לשתף כמה שטוב לך :\)\n\nכעת יש לבחור את רמת ההרשאות המתאימה לך\.\n*צפייה* או *עריכה*\.\n\(בכל מקרה לאף אחד מלבדך *לא* ניתן את האפשרות למחוק מתכון\)"

    await query.edit_message_text(
        f"{text}",
        reply_markup=InlineKeyboardMarkup(
            [share_buttons_permissions(unique_id), [cancel_button]]
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def share_link(update, context):
    query = update.callback_query
    await query.answer()

    query_data = query.data.split("_")
    unique_id = query_data[1]
    Permission_level = query_data[2]

    context.user_data["share"][unique_id]["permission_level"] = Permission_level

    new_sharing_info = context.user_data["share"][unique_id]

    # Save the unique_id in the database
    shares_handler.save_share_info(
        new_sharing_info["unique_id"],
        new_sharing_info["user_id"],
        new_sharing_info["permission_level"],
        new_sharing_info["link_status"],
        new_sharing_info["all_recipes"],
        new_sharing_info["recipe_id"],
    )
    user_handler.add_user_shared(new_sharing_info["user_id"], unique_id)

    share_link = f"`https://t.me/{context.bot.username}?start={unique_id}`"

    await query.edit_message_text(
        f"לחץ על הקישור כדי להעתיק אותו:\n {share_link}",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    if (
        "links_share_revoke" in context.user_data
        and new_sharing_info["permission_level"]
        in context.user_data["links_share_revoke"]
    ):
        context.user_data["links_share_revoke"]["link_revoke_ask"] = context.user_data[
            "links_share_revoke"
        ][new_sharing_info["permission_level"]]
        await query.message.reply_text(
            "האם תרצה לשמור או לבטל את הגישה למי ששיתפת בעזרת הלינק הישן?",
            reply_markup=InlineKeyboardMarkup(
                [
                    share_buttons_revoke_or_not(),
                    [cancel_button],
                ]
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )


async def revoke_user_shared(update, context):
    query = update.callback_query
    await query.answer()

    query_data = query.data.split("_")
    user_ansuer = query_data[1]

    old_link = context.user_data["links_share_revoke"]["link_revoke_ask"]
    if user_ansuer == "revoke":
        shares_handler.revoke_share_link(old_link["unique_id"])
        if "user_id_shared" in old_link:
            for user_id in old_link["user_id_shared"]:
                user_handler.remove_share_recipe(user_id, old_link["unique_id"])
            await query.edit_message_text(
                "השיתוף בוטל בהצלחה",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        else:
            await query.edit_message_text(
                "לא היה למי לבטל 🙄",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
    else:
        shares_handler.revoke_share_link(old_link["unique_id"])
        await query.edit_message_text(
            "כרצונך\. לא נוגעים 🤷‍♂️",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


async def update_accessable_recipes(update, context):
    user_id = str(update.effective_user.id)

    all_public_recipes = recipe_handler.fetch_public_recipes()
    owned_recipes = user_handler.fetch_owned_recipes(user_id)
    shared_recipes_info = user_handler.fetch_shared_recipes(user_id)

    shared_recipes = set()
    shared_recipe_permissions = {}

    for shared_info in shared_recipes_info:
        shared_info = shares_handler.fetch_share_info(shared_info)
        if shared_info:
            if shared_info["all_recipes"]:
                user_shared_recipes = user_handler.fetch_owned_recipes(
                    shared_info["user_id"]
                )
                shared_recipes.update(user_shared_recipes)

                for recipe in user_shared_recipes:
                    if (
                        recipe not in shared_recipe_permissions
                        or shared_info["permission_level"] == "edit"
                    ):
                        shared_recipe_permissions[recipe] = shared_info[
                            "permission_level"
                        ]
            else:
                shared_recipes.add(shared_info["recipe_id"])
                if (
                    shared_info["recipe_id"] not in shared_recipe_permissions
                    or shared_info["permission_level"] == "edit"
                ):
                    shared_recipe_permissions[shared_info["recipe_id"]] = shared_info[
                        "permission_level"
                    ]

    context.user_data["shared_recipe_permissions"] = shared_recipe_permissions

    public_recipes = [
        recipe
        for recipe in all_public_recipes
        if recipe["recipe_id"] not in owned_recipes
        and recipe["recipe_id"] not in shared_recipes
    ]

    return owned_recipes, shared_recipes, public_recipes


# inline mode
async def inline_query(update, context):
    user_query = update.inline_query.query
    print(user_query)
    user_id = str(update.inline_query.from_user.id)

    # Retrieve matching recipes from database
    owned_recipes = user_handler.fetch_owned_recipes(user_id)
    print(owned_recipes)
    # owned_recipes, shared_recipes, public_recipes = await update_accessable_recipes(
    #     update, context
    # )

    matching_recipes_owned = recipe_handler.search_recipes_by_name(
        owned_recipes, user_query
    )
    print(matching_recipes_owned)
    # matching_recipes_shared = recipe_handler.search_recipes_by_name(
    #     shared_recipes, user_query
    # )
    # matching_recipes_publicd = local_search_recipes_by_name(public_recipes, user_query)

    # Send the search results to the user
    results = []
    if matching_recipes_owned: # or matching_recipes_shared or matching_recipes_publicd:
        # if matching_recipes_owned:
        
        for recipe in matching_recipes_owned:
            
            if type(recipe["ingredients"]) != list:
                    recipe["ingredients"] = [
                        ingredient.strip() for ingredient in recipe["ingredients"].split(",")
                    ]

            formatted_ingredients = "\n".join(
                [
                    f"{index+1}.  {ingredient}"
                    for index, ingredient in enumerate(recipe["ingredients"])
                ]
            )

            recipe_str = f'*שם:*  {escape_markdown(recipe["recipe_name"], 2)}\n\n*רכיבים:*  {escape_markdown(formatted_ingredients, 2)}\n\n*הוראות:*  {escape_markdown(recipe["instructions"],2 )}'

            result = InlineQueryResultArticle(
                id=recipe["recipe_id"],
                title=recipe["recipe_name"],
                input_message_content=InputTextMessageContent(
                    message_text=recipe_str, parse_mode="MarkdownV2"
                ),
                thumb_url="https://picsum.photos/200/300",
            )
            results.append(result)
        # if matching_recipes_shared:
        #     for recipe in matching_recipes_shared:
        #         recipe_str = f'*שם:*  {recipe["recipe_name"]}\n\n*רכיבים:*  {recipe["ingredients"]}\n\n*הוראות:*  {recipe["instructions"]}'

        #         result = InlineQueryResultArticle(
        #             id=recipe["recipe_id"],
        #             title=recipe["recipe_name"],
        #             input_message_content=InputTextMessageContent(
        #                 message_text=recipe_str, parse_mode="Markdown_V2MARKDOWN_V2"
        #             ),
        #             thumb_url="https://picsum.photos/200/300",
        #         )
        #         results.append(result)
        # if matching_recipes_publicd:
        #     for recipe in matching_recipes_publicd:
        #         recipe_str = f'*שם:*  {recipe["recipe_name"]}\n\n*רכיבים:*  {recipe["ingredients"]}\n\n*הוראות:*  {recipe["instructions"]}'

        #         result = InlineQueryResultArticle(
        #             id=recipe["recipe_id"],
        #             title=recipe["recipe_name"],
        #             input_message_content=InputTextMessageContent(
        #                 message_text=recipe_str, parse_mode="Markdown_V2MARKDOWN_V2"
        #             ),
        #             thumb_url="https://picsum.photos/200/300",
        #         )
        #         results.append(result)    # inline query results

    await context.bot.answer_inline_query(update.inline_query.id, results)
