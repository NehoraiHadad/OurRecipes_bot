from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from models import (
    add_recipe_callback,
    get_recipe_name,
    get_ingredients,
    get_photo,
    get_instructions,
    cancel,
    search_recipe_callback,
    get_user_search,
    edit_recipe,
    edit_recipe_get_respond,
    delete_recipe,
    more_details,
    share_callback,
    share_permission_level,
    share
)

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
txt_share_button_en_1 = "b-share-1"
txt_share_button_en_2 = "b-share-2"
txt_share_button_en_3 = "b-share-3"
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
SHARE_PERMISSIONS, SHARE = range(2)


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
        CallbackQueryHandler(search_recipe_callback, pattern=txt_search_recipe)
    ],
    states={
        USER_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_search)],
        TRY_AGAIN: [
            CallbackQueryHandler(search_recipe_callback, pattern=txt_try_again)
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

share_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(share_callback, pattern=txt_share_button_en_1)],
    states={
        SHARE_PERMISSIONS: [
            CallbackQueryHandler(share_permission_level, pattern=txt_share_button_en_2)
        ],
        SHARE: [
            CallbackQueryHandler(
                share, pattern=txt_share_button_en_3
            )
        ]
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern=txt_cancel)],
)
more_details_handler = CallbackQueryHandler(more_details, pattern=txt_more_details)