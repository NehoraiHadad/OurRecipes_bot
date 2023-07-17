from modules.dynamoDB import RecipeHandler, SharesHandler, UserHandler
from telegram.constants import ParseMode


user_handler = UserHandler("users")
recipe_handler = RecipeHandler("recipes")
shares_handler = SharesHandler("shares")


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

    if "public" in context.user_data["share"]:
        del context.user_data["share"]

    return