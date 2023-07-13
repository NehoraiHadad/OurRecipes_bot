from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CommandHandler,
)

from models import (
    add_recipe_callback,
    get_recipe_name,
    get_ingredients,
    get_photo,
    get_instructions,
    cancel,
    revoke_user_shared,
    search_recipe_callback,
    get_user_search,
    edit_recipe,
    edit_recipe_get_respond,
    delete_recipe,
    more_details,
    share_callback,
    share_link,
    share_permission_level,
    share_public_state,
    share_togglt_public,
)

# text
txt_add_recipe = "הוסף מתכון חדש"
txt_search_recipe = "חפש מתכון"

txt_cancel = "בטל 🛑"
txt_try_again = "לנסות שוב? 🔄"
txt_try_again_en = "try_again"
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
txt_share_single = "share single"
txt_share_all = "share all"
txt_share_link = "יצירת לינק"
txt_share_link_en = "link"
txt_share_public = "שתף לכולם"
txt_share_public_en = "public"
txt_share_edit = "עריכה"
txt_share_edit_en = "edit"
txt_share_view = "צפייה"
txt_share_view_en = "view"


# state for conv handler
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_PHOTO = range(4)
USER_QUERY, TRY_AGAIN = range(2)
GET_NEW_VALUE, GET_DELETE_RECIPE = range(2)


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
