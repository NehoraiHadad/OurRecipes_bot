from telegram import InlineKeyboardMarkup

from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from modules.s3 import download_photo_from_s3

from modules.helpers.buttons import edit_recipe_button, more_details_button, share_button

from modules.helpers.txt import (txt_share_single)


async def display_recipe(update, context, recipe, is_shared=False, is_public=False):
    context.user_data[recipe["recipe_id"]] = recipe

    if type(recipe["ingredients"]) != list:
        recipe["ingredients"] = [
            ingredient.strip() for ingredient in recipe["ingredients"].split(",")
        ]

    formatted_ingredients = "\n".join(
        [
            f"{index+1}.  {ingredient}"
            for index, ingredient in enumerate(recipe["ingredients"])
        ]
    )
    recipe_str = f'*שם:*  {escape_markdown(recipe["recipe_name"], 2)}\n\n*רכיבים:*\n{escape_markdown(formatted_ingredients, 2)}\n\n*הוראות:*\n{escape_markdown(recipe["instructions"], 2)}'

    message = None
    if recipe["photo_url"]:
        photo = download_photo_from_s3(recipe["photo_url"])
        message = await context.bot.send_photo(
            update.effective_chat.id,
            photo=photo,
            caption=recipe_str,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        await edit_recipe_button(recipe["recipe_id"]),
                        await more_details_button(recipe["recipe_id"]),
                    ],
                    [
                        await share_button(
                            is_all_or_single=txt_share_single,
                            recipe_id=recipe["recipe_id"],
                        )
                    ],
                ],
            )
            if not is_shared and not is_public
            else None,
        )
    else:
        message = await update.message.reply_text(
            recipe_str,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        await edit_recipe_button(recipe["recipe_id"]),
                        await more_details_button(recipe["recipe_id"]),
                    ],
                    [
                        await share_button(
                            is_all_or_single=txt_share_single,
                            recipe_id=recipe["recipe_id"],
                        )
                    ],
                ],
            )
            if not is_shared and not is_public
            else None,
        )

    if is_shared:
        await update_message_with_permissions(context, message, recipe["recipe_id"])


async def update_message_with_permissions(context, message, recipe_id):
    shared_recipe_permission = context.user_data["shared_recipe_permissions"].get(
        recipe_id
    )
    if shared_recipe_permission == "edit":
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    await edit_recipe_button(recipe_id),
                    await more_details_button(recipe_id),
                ]
            ]
        )

        await context.bot.edit_message_reply_markup(
            chat_id=message.chat_id,
            message_id=message.message_id,
            reply_markup=reply_markup,
        )