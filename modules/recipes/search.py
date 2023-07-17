from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.dynamoDB import RecipeHandler
from telegram.ext import ConversationHandler

from modules.helpers.sticker_loader import start_sticker_loader, stop_sticker_loader
from modules.helpers.update_accessable_recipes import update_accessable_recipes
from modules.recipes.display import display_recipe
from modules.helpers.buttons import cancel_button

recipe_handler = RecipeHandler("recipes")


txt_try_again = "לנסות שוב? 🔄"
txt_try_again_en = "try_again"


USER_QUERY, TRY_AGAIN = range(2)


async def search_recipe_callback(update, context):
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "מה לחפש?", reply_markup=InlineKeyboardMarkup([[cancel_button()]])
        )
    else:
        await update.effective_chat.send_message(
            "מה לחפש?", reply_markup=InlineKeyboardMarkup([[cancel_button()]])
        )
    return USER_QUERY

async def get_user_search(update, context):
    user_query = update.message.text

    stiker_message = await start_sticker_loader(update, context)
    
    # Perform the search and retrieve matching recipes from DB
    owned_recipes, shared_recipes, public_recipes = await update_accessable_recipes(
        update, context
    )

    matching_recipes_owned = await recipe_handler.search_recipes_by_name(
        owned_recipes, user_query
    )
    matching_recipes_shared = await recipe_handler.search_recipes_by_name(
        shared_recipes, user_query
    )
    matching_recipes_publicd = local_search_recipes_by_name(public_recipes, user_query)

    await stop_sticker_loader(update, context, stiker_message = stiker_message)

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
                        cancel_button(),
                        InlineKeyboardButton(
                            txt_try_again, callback_data=txt_try_again_en
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
