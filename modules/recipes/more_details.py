from telegram import InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

import datetime

from modules.helpers.buttons import edit_recipe_button
from modules.helpers.text_effects import add_words_bold


txt_more_details = "פרטים נוספים"


async def more_details(update, context):
    query = update.callback_query
    await query.answer()

    recipe_id = query.data.replace(txt_more_details, "")
    recipe = context.user_data[recipe_id]

    bold_words = ["שם:", "רכיבים:", "הוראות:"]

    date_format = "%Y-%m-%d %H:%M:%S"

    if recipe["recipe_modified"] != "":
        str_modified = recipe["recipe_modified"]
        str_modified = escape_markdown(
            str(datetime.datetime.strptime(str_modified, date_format)), 2
        )
    else:
        str_modified = "המתכון לא עבר שינוי"

    created_by = escape_markdown(
        str(datetime.datetime.strptime(recipe["recipe_created"], date_format)), 2
    )
    more_details_str = (
        f"\n\n*תאריך הוספה:*  {created_by}\n\n*תאריך שינוי:*  {str_modified}"
    )

    if query.message.photo:
        caption_bold = add_words_bold(query.message.caption, bold_words)
        await query.message.edit_caption(
            caption=f"{caption_bold}{more_details_str}",
            reply_markup=InlineKeyboardMarkup([[await edit_recipe_button(recipe_id)]]),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        text_bold = add_words_bold(query.message.text, bold_words)
        await query.message.edit_text(
            text=f"{text_bold}{more_details_str}",
            reply_markup=InlineKeyboardMarkup([[await edit_recipe_button(recipe_id)]]),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
