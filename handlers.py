from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CommandHandler,
    InlineQueryHandler,
)

from modules.commands import start, unknown
from modules.helpers.cancel import cancel
from modules.inline_mode import inline_query
from modules.recipes.more_details import more_details
from modules.recipes.add import (
    add_recipe_callback,
    get_ingredients,
    get_instructions,
    get_photo,
    get_recipe_name,
)
from modules.recipes.delete import delete_recipe
from modules.recipes.edit import edit_recipe, edit_recipe_get_respond
from modules.recipes.search import get_user_search, search_recipe_callback
from modules.share.link import share_link, share_permission_level
from modules.share.public import share_public_state, share_togglt_public
from modules.share.revoke import revoke_user_shared
from modules.share.share import share_callback

from modules.helpers.txt import (
    txt_add_recipe,
    txt_search_recipe,
    txt_cancel,
    txt_edit,
    txt_more_details,
    txt_share_button_start_en,
    txt_share_button_public_en,
    txt_share_button_link_en,
    txt_share_button_togglt_public_en,
    txt_share_button_create_link_en,
    txt_share_button_revoke_or_not,
    txt_try_again_en
)

# state for conv handler
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_PHOTO = range(4)
USER_QUERY, TRY_AGAIN = range(2)
GET_NEW_VALUE, GET_DELETE_RECIPE = range(2)


start_handler = CommandHandler("start", start)
inline_query_handler = InlineQueryHandler(inline_query)
unknown_handler = MessageHandler(filters.COMMAND, unknown)

add_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_recipe_callback, pattern=txt_add_recipe)],
    states={
        RECIPE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipe_name)],
        RECIPE_INGREDIENTS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_ingredients)
        ],
        RECIPE_PHOTO: [MessageHandler(filters.ALL & ~filters.COMMAND, get_photo)],
        RECIPE_INSTRUCTIONS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_instructions)
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern=txt_cancel)],
    allow_reentry=True,
)

search_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(search_recipe_callback, pattern=txt_search_recipe),
        CommandHandler("search", search_recipe_callback),
    ],
    states={
        USER_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_search)],
        TRY_AGAIN: [
            CallbackQueryHandler(search_recipe_callback, pattern=txt_try_again_en)
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern=txt_cancel)],
    allow_reentry=True,
)

edit_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(edit_recipe, pattern=txt_edit)],
    states={
        GET_NEW_VALUE: [
            MessageHandler(
                filters.TEXT | filters.PHOTO & ~filters.COMMAND, edit_recipe_get_respond
            )
        ],
        GET_DELETE_RECIPE: [
            CallbackQueryHandler(delete_recipe, pattern="OK to delete"),
            CallbackQueryHandler(cancel, pattern=txt_cancel),
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern=txt_cancel)],
)

# share handlers { ----
share_start_handler = CallbackQueryHandler(
    share_callback, pattern=txt_share_button_start_en
)

share_public_state_handler = CallbackQueryHandler(
    share_public_state, pattern=txt_share_button_public_en
)

share_public_togglt_handler = CallbackQueryHandler(
    share_togglt_public, pattern=txt_share_button_togglt_public_en
)

share_permission_level_handler = CallbackQueryHandler(
    share_permission_level, pattern=txt_share_button_link_en
)

share_link_handler = CallbackQueryHandler(
    share_link, pattern=txt_share_button_create_link_en
)

share_revoke_user_shared_handler = CallbackQueryHandler(
    revoke_user_shared, pattern=txt_share_button_revoke_or_not
)
# ---- }

more_details_handler = CallbackQueryHandler(more_details, pattern=txt_more_details)
