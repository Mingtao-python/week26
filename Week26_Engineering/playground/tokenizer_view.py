import re

class TokenizerView:
    def tokenize(self, text):
        tokens = re.findall(r"\w+|\S", text)
        return tokens
