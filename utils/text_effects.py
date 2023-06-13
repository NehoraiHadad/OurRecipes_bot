def add_words_bold(text, bold_words):
    for word in bold_words:
        text = text.replace(word, f'*{word}*')
    
    return text