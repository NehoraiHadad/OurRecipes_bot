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

from dynamoDB import RecipeHandler, UserHandler, PermissionsHandler
from s3 import upload_photo_to_s3, download_photo_from_s3, delete_photo_from_s3

from utils.text_effects import add_words_bold

user_handler = UserHandler("users")
recipe_handler = RecipeHandler("recipes")
permissions_handler = PermissionsHandler("permissions")


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
txt_share_recipe = "שיתוף"
txt_share_single = "share single"
txt_share_all = "share all"
txt_share_link = "יצירת לינק"
txt_share_link_en = "link"
txt_share_public = "שתף לכולם"
txt_share_public_en = "public"


# state for conv handler
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_PHOTO = range(4)
USER_QUERY, TRY_AGAIN = range(2)
GET_NEW_VALUE, GET_DELETE_RECIPE = range(2)

# buttons
cancel_button = InlineKeyboardButton(txt_cancel, callback_data=txt_cancel)
def init_buttons():
    init_buttons = [
    [InlineKeyboardButton(txt_add_recipe, callback_data=txt_add_recipe)],
    [InlineKeyboardButton(txt_search_recipe, callback_data=txt_search_recipe)],
    share_button(is_all_or_single=txt_share_all),
    ]
    return(init_buttons)


def edit_buttons(context, recipe_id):
    recipe = context.user_data[recipe_id]
    if recipe["created_by"] == context.user_date["user_id"]:
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
        )
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
        ]
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
        )
        [
            InlineKeyboardButton(
                txt_edit_instructions,
                callback_data=f"{txt_edit}_{txt_edit_instructions}_{recipe_id}",
            ),
            InlineKeyboardButton(
                txt_edit_photo, callback_data=f"{txt_edit}_{txt_edit_photo}_{recipe_id}"
            ),
        ]
    return bottons


def edit_recipe_button(recipe_id):
    return InlineKeyboardButton(
        txt_edit_recipe, callback_data=f"{txt_edit_recipe}{recipe_id}"
    )

def more_details_button(recipe_id):
    return InlineKeyboardButton(
        txt_more_details, callback_data=f"{txt_more_details}{recipe_id}"
    )

def share_button(is_all_or_single, recipe_id = None):
    return InlineKeyboardButton(
        txt_share_recipe, callback_data=is_all_or_single + ("_" + recipe_id if recipe_id is not None else "")
    )

def share_buttons(is_all_or_single, recipe_id = None):
    return InlineKeyboardButton(
        txt_share_link, callback_data = is_all_or_single + "_" + txt_share_link_en + '_' + recipe_id if recipe_id else ""
    ), InlineKeyboardButton(
        txt_share_public, callback_data = is_all_or_single + "_" + txt_share_public_en + '_' + recipe_id if recipe_id else ""
        )


# commends
def start(update, context):
    user_id = str(update.message.from_user.id)
    username = update.effective_user.first_name
    context.user_data["user_id"] = user_id
    context.user_data["user_name"] = username
    shared_recipes = []

    if context.args:
        unique_id = context.args[0]
        share_info = PermissionsHandler.fetch_share_info(unique_id)
        if share_info["user_id"]:
            if share_info["user_id"] == user_id:
                update.message.reply_text("אין אפשרות לשתף מתכון עם עצמך :)")
                return
            if share_info["recipe_id"] or share_info["all_recipes"]:
                PermissionsHandler.add_share_access(user_id)
                shared_recipes.append(unique_id)
                update.message.reply_text(
                    "שותפת עם מתכון!"
                    if share_info["recipe_id"]
                    else "שותפת עם מלא מתכונים!"
                )

    response = user_handler.register_user(user_id, username, shared_recipes)

    if response:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"שלום {username}!\nאני בוט מתכונים! בו ניתן להוסיף לערוך ולחפש את המתכונים בצורה נוחה...",
            reply_markup=InlineKeyboardMarkup(init_buttons),
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="יש לנו בעיה... יש ללחוץ שוב על /start",
        )


def unknown(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="לא מכיר את הפקודה הזו  ):"
    )


# display functions
def display_recipe(update, context, recipe, is_shared = False):
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

    message = None
    if recipe["photo_url"] != None:
        photo = download_photo_from_s3(recipe["photo_url"])
        message = context.bot.send_photo(
            update.effective_chat.id,
            photo=photo,
            caption=recipe_str,
            parse_mode=ParseMode.MARKDOWN,    
            reply_markup = InlineKeyboardMarkup(
            [[edit_recipe_button(recipe["recipe_id"]), more_details_button(recipe["recipe_id"])]],[[share_button(recipe["recipe_id"], txt_share_single)]]
        ) if not is_shared else None
        )
    else:
        message = update.message.reply_text(
            recipe_str,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup = InlineKeyboardMarkup(
            [[edit_recipe_button(recipe["recipe_id"]), more_details_button(recipe["recipe_id"])]],[[share_button(recipe["recipe_id"], txt_share_single)]]
        ) if not is_shared else None
        )

    if is_shared:
        update_message_with_permissions(
            context, message, recipe["recipe_id"]
        )


async def update_message_with_permissions(
    context, message, recipe_id
):
    shared_recipe_permission = context.user_data["shared_recipe_permissions"].get(recipe_id)
    if shared_recipe_permission == "view":
        reply_markup = None  # No buttons for view only
    elif shared_recipe_permission == "edit":
        reply_markup = InlineKeyboardMarkup(
            [[edit_recipe_button(recipe_id), more_details_button(recipe_id)]]
        )

    await context.bot.edit_message_reply_markup(
        chat_id=message.chat_id,
        message_id=message.message_id,
        reply_markup=reply_markup,
    )


# add recipe


def add_recipe_callback(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        "שם המתכון:", reply_markup=InlineKeyboardMarkup([[cancel_button]])
    )
    return RECIPE_NAME


def get_recipe_name(update, context):
    name = update.message.text
    context.user_data["recipe_name"] = name
    update.message.reply_text(
        "יש תמונה? (אם לא, כתוב ושלח משהו)",
        reply_markup=InlineKeyboardMarkup([[cancel_button]]),
    )
    return RECIPE_PHOTO


def get_photo(update, context):
    if update.message.photo:
        # Photo received
        photo_id = update.message.photo[-1].file_id
        photo = context.bot.get_file(photo_id)

        # Create an in-memory file-like object to store the photo data
        photo_data = io.BytesIO()
        photo.download_to_memory(out=photo_data)
        photo_data.seek(0)

        context.user_data["recipe_photo"] = photo_data

        update.message.reply_text(
            "הרכיבים (מופרדים בפסיק):",
            reply_markup=InlineKeyboardMarkup([[cancel_button]]),
        )
        return RECIPE_INGREDIENTS
    else:
        # No photo received, proceed without photo
        context.user_data["recipe_photo"] = ""

        update.message.reply_text(
            "הרכיבים (מופרדים בפסיק):",
            reply_markup=InlineKeyboardMarkup([[cancel_button]]),
        )
        return RECIPE_INGREDIENTS


def get_ingredients(update, context):
    ingredients = update.message.text
    context.user_data["recipe_ingredients"] = ingredients
    update.message.reply_text(
        "הוראות:", reply_markup=InlineKeyboardMarkup([[cancel_button]])
    )
    return RECIPE_INSTRUCTIONS


def get_instructions(update, context):
    instructions = update.message.text
    context.user_data["recipe_instructions"] = instructions
    user_id = context.user_data["user_id"]
    photo_data = context.user_data["recipe_photo"]

    recipe_id = str(uuid.uuid4())
    photo_url = upload_photo_to_s3(photo_data, recipe_id)

    current_date = datetime.datetime.now()
    date_format = "%Y-%m-%d %H:%M:%S"
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
    display_recipe(update, context, recipe)

    context.user_data[recipe_id] = recipe
    update.message.reply_text(
        "מה עוד?", reply_markup=InlineKeyboardMarkup(init_buttons)
    )
    return ConversationHandler.END


def cancel(update, context):
    update.callback_query.edit_message_text("הפעולה בוטלה.")
    update.callback_query.message.reply_text(
        "מה עוד?", reply_markup=InlineKeyboardMarkup(init_buttons)
    )

    # context.user_data.clear()  -- I need to use pop instead clear method
    return ConversationHandler.END


# search recipe
def search_recipe_callback(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        "מה לחפש?", reply_markup=InlineKeyboardMarkup([[cancel_button]])
    )
    return USER_QUERY


def get_user_search(update, context):
    user_query = update.message.text
    context.user_data["user_query"] = user_query
    user_id = context.user_data["user_id"]

    # Perform the search and retrieve matching recipes from DB
    owned_recipes = user_handler.get_owned_recipes(user_id)
    shared_recipes_info = user_handler.get_shared_recipes(user_id)
    shared_recipes = []
    shared_recipe_permissions = {}

    for shared_recipe_info in shared_recipes_info:
        shared_recipe_info = permissions_handler.fetch_share_info(shared_recipe_info)
        if shared_recipe_info:
            if shared_recipe_info["all_recipes"]:
                user_shared_recipes = user_handler.get_owned_recipes(shared_recipe_info["user_id"])
                shared_recipes.extend(user_shared_recipes)

                for recipe in user_shared_recipes:
                        shared_recipe_permissions[recipe["recipe_id"]] = shared_recipe_info["permission_level"]
     
            elif shared_recipe_info:
                shared_recipes.append(shared_recipe_info["recipe_id"])
                shared_recipe_permissions[shared_recipe_info["recipe_id"]] = shared_recipe_info["permission_level"]

    context.user_data["shared_recipe_permissions"] = shared_recipe_permissions

    matching_recipes_owned = recipe_handler.search_recipes_by_name(
        owned_recipes, user_query
    )
    matching_recipes_shared = recipe_handler.search_recipes_by_name(
        shared_recipes, user_query
    )

    # Send the search results to the user
    if matching_recipes_owned or matching_recipes_shared:
        if matching_recipes_owned:
            for recipe in matching_recipes_owned:
                display_recipe(update, context, recipe)
        if matching_recipes_shared:
            for recipe in matching_recipes_shared:
                display_recipe(update, context, recipe, True)
    else:
        update.message.reply_text(
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
def edit_recipe_callback(update, context):
    query = update.callback_query
    query.answer()

    recipe_id = query.data.replace(txt_edit_recipe, "")
    query.message.reply_text(
        text="אז מה לערוך?",
        reply_markup=InlineKeyboardMarkup(edit_buttons(recipe_id)),
    )
    message_id = query.message.message_id
    context.user_data["message_id"] = message_id


def edit_recipe(update, context):
    query = update.callback_query
    query.answer()
    action, recipe_id = query.data.split("_")[1:]

    context.user_data["recipe_id"] = recipe_id
    context.user_data["action"] = action

    if action == txt_edit_photo:
        query.edit_message_text(
            f"מחכה לשליחת תמונה חדשה",
            reply_markup=InlineKeyboardMarkup([[cancel_button]]),
        )
    elif (
        action == txt_edit_ingredients
        or action == txt_edit_instructions
        or action == txt_edit_name
    ):
        query.edit_message_text(
            f"נא להקליד את העדכון ב{action}:",
            reply_markup=InlineKeyboardMarkup([[cancel_button]]),
        )
    elif action == txt_delete:
        query.edit_message_text(
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


def edit_recipe_get_respond(update, context):
    message_id = context.user_data["message_id"]
    message_id_edit = context.user_data["message_id_edit"]
    message_id_user = update.message.message_id
    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
    context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=message_id_edit
    )
    context.bot.delete_message(
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
        photo = context.bot.get_file(new_photo_id)

        # Create an in-memory file-like object to store the photo data
        photo_data = io.BytesIO()
        photo.download_to_memory(out=photo_data)
        photo_data.seek(0)

        photo_url = upload_photo_to_s3(photo_data, recipe_id)
        if recipe["photo_url"] != "":
            delete_photo_from_s3(recipe["photo_url"])

        recipe["photo_url"] = photo_url
        update_data = {"photo_url": photo_url}

    if update_data != "":
        current_date = datetime.datetime.now()
        date_format = "%Y-%m-%d %H:%M:%S"
        date_string = current_date.strftime(date_format)
        recipe_modified = date_string

        update_data["recipe_modified"] = recipe_modified

        #  Update DB
        recipe_handler.update_recipe(recipe_id, update_data)
        update.message.reply_text("השינוי נשמר בהצלחה")

        # TO DO - In display_recipe function: change (just here) the recipe param to inclode the photo from user not from DB
        display_recipe(update, context, recipe)

    else:
        update.message.reply_text("לא נקלט שינוי")

    keys_to_clear = ["action", "recipe_id", "message_id_edit", "message_id"]
    for key in keys_to_clear:
        if key in context.user_data:
            del context.user_data[key]

    return ConversationHandler.END


def delete_recipe(update, context):
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

    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
    context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=message_id_edit
    )

    query.message.reply_text("המתכון נמחק בהצלחה")
    query.message.reply_text("מה עוד?", reply_markup=InlineKeyboardMarkup(init_buttons))

    return ConversationHandler.END


def more_details(update, context):
    query = update.callback_query
    query.answer()

    recipe_id = query.data.replace(txt_more_details, "")
    recipe = context.user_data[recipe_id]

    bold_words = ["שם:", "רכיבים:", "הוראות:"]

    date_format = "%Y-%m-%d %H:%M:%S"

    if recipe["recipe_modified"] != "":
        str_modified = recipe["recipe_modified"]
        str_modified = datetime.datetime.strptime(str_modified, date_format)
    else:
        str_modified = "המתכון לא עבר שינוי"

    created_by = datetime.datetime.strptime(recipe["recipe_created"], date_format)
    more_details_str = (
        f"\n\n*תאריך הוספה:*  {created_by}\n\n*תאריך שינוי:*  {str_modified}"
    )

    if query.message.photo:
        caption_bold = add_words_bold(query.message.caption, bold_words)
        query.message.edit_caption(
            caption=f"{caption_bold}{more_details_str}",
            reply_markup=InlineKeyboardMarkup([[edit_recipe_button(recipe_id)]]),
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        text_bold = add_words_bold(query.message.text, bold_words)
        query.message.edit_text(
            text=f"{text_bold}{more_details_str}",
            reply_markup=InlineKeyboardMarkup([[edit_recipe_button(recipe_id)]]),
            parse_mode=ParseMode.MARKDOWN,
        )

def share_callback(update, context):
    query = update.callback_query
    query.answer()

    sharing_info = {}

    query_data = query.data.split("_")
    recipe_id = query_data[1] if len(query_data) > 2 else None
    is_all_or_single = query_data[0]
    if is_all_or_single == txt_share_all:
        sharing_info["all"] = True
    else:
        sharing_info[recipe_id] = recipe_id

    query.reply_text(
        f"איך לשתף?\n\n*אפשרות* אחת לשתף לכולם\nאפשרות *אחרת* לשתף בעזרת קישור שניתן לשלוח למי שרוצים לשתף", reply_markup=InlineKeyboardMarkup([[share_buttons(is_all_or_single, recipe_id)],[cancel_button]])
    )


def share_permission_level(update, contect):
    query = update.callback_query
    query.answer()




def share_link(update, context):
    query = update.callback_query
    query.answer()

    query_data = query.data.split("_")
    is_all_or_single = query_data[0]
    recipe_id = query_data[2] if len(query_data) > 2 else None

    user_id = update.effective_user.id

    # permission_level = context.user_data["permission_level"]
    all_recipes = is_all_or_single == txt_share_all
    recipe_id = context.user_data["recipe_to_share"] if is_all_or_single == txt_share_single else None
    unique_id = str(uuid.uuid4())

    # Save the unique_id in the database
    permissions_handler.save_share_link(
        unique_id, user_id, permission_level, all_recipes, recipe_id
    )

    share_link = f"`https://t.me/{context.bot.username}?start={unique_id}`"

    query.edit_message_text(
        f"הנה הקישור לשיתוף: {share_link}", parse_mode=ParseMode.MARKDOWN
    )


# inline mode
def inline_query(update, context):
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

    context.bot.answer_inline_query(update.inline_query.id, results)
