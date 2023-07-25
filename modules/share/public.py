
from telegram import InlineKeyboardMarkup
from telegram.constants import ParseMode
from modules.dynamoDB import RecipeHandler, SharesHandler, UserHandler

user_handler = UserHandler("users")
recipe_handler = RecipeHandler("recipes")
shares_handler = SharesHandler("shares")

from modules.helpers.buttons import share_buttons_public_or_privet, cancel_button


async def share_public_state(update, context):
    query = update.callback_query
    await query.answer()

    is_public = context.user_data["share"]["public"]["is_public"]
    state = "ציבורי" if not is_public else "פרטי"

    text = f"בטוח שתרצה להפוך ל{state}?"

    return await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [share_buttons_public_or_privet(is_public), [cancel_button()]]
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def share_togglt_public(update, context):
    query = update.callback_query

    public_info = context.user_data["share"]["public"]
    user_id = str(update.effective_user.id)

    if public_info["all_recipes"]:
        if public_info["is_public"]:
            await recipe_handler.revoke_all_public(user_id)
            user_handler.update_all_recipes_public(user_id, False)
            text = "המתכונים שלך פרטיים עכשיו"
        else:
            await recipe_handler.make_all_public(user_id)
            user_handler.update_all_recipes_public(user_id, True)
            text = "כל המתכונים שלך ציבוריים עכשיו!\n נחמד מצידך 🙂"

        await query.edit_message_text(text)

    else:
        if public_info["is_public"]:
            await recipe_handler.revoke_public(public_info["recipe_id"])
            text = "המתכון שלך פרטי עכשיו"
        else:
            await recipe_handler.make_public(public_info["recipe_id"])
            text = "המתכון שלך ציבורי עכשיו!\n נחמד מצידך 🙂"

        await query.edit_message_text(text)

    if "public" in context.user_data["share"]:
        del context.user_data["share"]["public"]
    
    return

