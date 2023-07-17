from telegram.helpers import escape_markdown

def add_words_bold(text, bold_words):
    text = escape_markdown(text, 2)
    for word in bold_words:
        text = text.replace(word, f'*{word}*')
    
    return text