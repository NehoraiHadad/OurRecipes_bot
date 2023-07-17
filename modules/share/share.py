from telegram import InlineKeyboardMarkup
from telegram.constants import ParseMode


import datetime

from modules.dynamoDB import RecipeHandler, SharesHandler, UserHandler

import uuid

from modules.helpers.buttons import share_buttons_link_or_public,cancel_button

user_handler = UserHandler("users")
recipe_handler = RecipeHandler("recipes")
shares_handler = SharesHandler("shares")



txt_share_all = "share-all"


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
                if "links_share_revoke" not in context.user_data:
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