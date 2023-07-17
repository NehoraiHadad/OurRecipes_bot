from telegram import InlineKeyboardMarkup
from modules.dynamoDB import RecipeHandler, SharesHandler, UserHandler
from modules.helpers.buttons import init_buttons


user_handler = UserHandler("users")
shares_handler = SharesHandler("shares")

async def start(update, context):
    user_id = str(update.effective_user.id)
    username = update.effective_user.first_name
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
