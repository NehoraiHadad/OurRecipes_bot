# buttons
from telegram import InlineKeyboardButton

# text
txt_add_recipe = "הוסף מתכון חדש"
txt_search_recipe = "חפש מתכון"

txt_cancel = "בטל 🛑"

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

txt_share_all = "share-all"
txt_share_link = "יצירת לינק"
txt_share_link_en = "link"
txt_share_public = "ציבורי/פרטי"
txt_share_public_en = "public"
txt_share_edit = "עריכה"
txt_share_edit_en = "edit"
txt_share_view = "צפייה"
txt_share_view_en = "view"


def cancel_button():
    return InlineKeyboardButton(txt_cancel, callback_data=txt_cancel)


async def init_buttons():
    init_buttons = [
        [InlineKeyboardButton(txt_add_recipe, callback_data=txt_add_recipe)],
        [InlineKeyboardButton(txt_search_recipe, callback_data=txt_search_recipe)],
        [await share_button(is_all_or_single=txt_share_all)],
    ]
    return init_buttons


def edit_buttons(update, context, recipe_id):
    recipe = context.user_data[recipe_id]
    user_id = str(update.effective_user.id)
    if recipe["created_by"] == user_id:
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

