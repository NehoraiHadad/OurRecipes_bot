
from telegram.constants import ParseMode
from telegram import InlineKeyboardMarkup

from modules.dynamoDB import SharesHandler, UserHandler
from modules.helpers.buttons import share_buttons_permissions, cancel_button, share_buttons_revoke_or_not

user_handler = UserHandler("users")
shares_handler = SharesHandler("shares")


txt_share_link_en = "link"


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

    return await query.edit_message_text(
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
        return
    
    if "public" in context.user_data["share"]:
        del context.user_data["share"]

    return