from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ',
    'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
    'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
    'y': 'ʏ', 'z': 'ᴢ',
    'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ', 'H': 'ʜ',
    'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ',
    'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x',
    'Y': 'ʏ', 'Z': 'ᴢ',
}

def to_small_caps(text: str) -> str:
    if not text:
        return ""
    return "".join(SMALL_CAPS_MAP.get(c, c) for c in str(text))


def format_btn_text(text: str, small_cap: bool = False) -> str:
    return to_small_caps(text) if small_cap else str(text)


class ButtonMaker:
    def __init__(self):
        self.__button = []
        self.__header_button = []
        self.__first_body_button = []
        self.__last_body_button = []
        self.__footer_button = []

    def ubutton(self, key, link, position=None, small_cap=False, style=None):
        btn_text = format_btn_text(key, small_cap)
        btn = InlineKeyboardButton(text=btn_text, url=link)
        if style and str(style).lower() in ["primary", "success", "danger"]:
            btn.style = str(style).lower()
        if not position:
            self.__button.append(btn)
        elif position == "header":
            self.__header_button.append(btn)
        elif position == "f_body":
            self.__first_body_button.append(btn)
        elif position == "l_body":
            self.__last_body_button.append(btn)
        elif position == "footer":
            self.__footer_button.append(btn)

    def ibutton(self, key, data, position=None, small_cap=False, style=None):
        btn_text = format_btn_text(key, small_cap)
        btn = InlineKeyboardButton(text=btn_text, callback_data=data)
        if style and str(style).lower() in ["primary", "success", "danger"]:
            btn.style = str(style).lower()
        if not position:
            self.__button.append(btn)
        elif position == "header":
            self.__header_button.append(btn)
        elif position == "f_body":
            self.__first_body_button.append(btn)
        elif position == "l_body":
            self.__last_body_button.append(btn)
        elif position == "footer":
            self.__footer_button.append(btn)

    def build_menu(self, b_cols=1, h_cols=8, fb_cols=2, lb_cols=2, f_cols=8):
        menu = [
            self.__button[i : i + b_cols] for i in range(0, len(self.__button), b_cols)
        ]
        if self.__header_button:
            if len(self.__header_button) > h_cols:
                header_buttons = [
                    self.__header_button[i : i + h_cols]
                    for i in range(0, len(self.__header_button), h_cols)
                ]
                menu = header_buttons + menu
            else:
                menu.insert(0, self.__header_button)
        if self.__first_body_button:
            if len(self.__first_body_button) > fb_cols:
                [
                    menu.append(self.__first_body_button[i : i + fb_cols])
                    for i in range(0, len(self.__first_body_button), fb_cols)
                ]
            else:
                menu.append(self.__first_body_button)
        if self.__last_body_button:
            if len(self.__last_body_button) > lb_cols:
                [
                    menu.append(self.__last_body_button[i : i + lb_cols])
                    for i in range(0, len(self.__last_body_button), lb_cols)
                ]
            else:
                menu.append(self.__last_body_button)
        if self.__footer_button:
            if len(self.__footer_button) > f_cols:
                [
                    menu.append(self.__footer_button[i : i + f_cols])
                    for i in range(0, len(self.__footer_button), f_cols)
                ]
            else:
                menu.append(self.__footer_button)
        return InlineKeyboardMarkup(menu)


def to_bot_api_keyboard(reply_markup):
    if not reply_markup or not hasattr(reply_markup, "inline_keyboard"):
        return None
    raw_keyboard = []
    has_style = False
    for row in reply_markup.inline_keyboard:
        raw_row = []
        for btn in row:
            b_dict = {"text": btn.text}
            if getattr(btn, "callback_data", None) is not None:
                b_dict["callback_data"] = (
                    btn.callback_data
                    if isinstance(btn.callback_data, str)
                    else btn.callback_data.decode("utf-8", errors="ignore")
                )
            if getattr(btn, "url", None) is not None:
                b_dict["url"] = btn.url
            if hasattr(btn, "style") and btn.style in ["primary", "success", "danger"]:
                b_dict["style"] = btn.style
                has_style = True
            raw_row.append(b_dict)
        raw_keyboard.append(raw_row)
    return {"inline_keyboard": raw_keyboard} if has_style else None
