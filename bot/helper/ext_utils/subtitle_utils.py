#!/usr/bin/env python3
"""
Subtitle utilities for intro subtitle feature.
Handles FFmpeg character escaping and subtitle file generation.
"""


def escape_subtitle_text(text):
    """
    Escape ALL special characters for FFmpeg drawtext filter.
    
    FFmpeg drawtext requires escaping for many special characters
    that could break the filter syntax.
    
    Args:
        text: Raw subtitle text input from user
        
    Returns:
        str: Escaped text safe for FFmpeg drawtext filter
    """
    # Order matters! Backslash must be escaped first
    text = text.replace("\\", "\\\\")      # Backslash
    text = text.replace("'", "\\'")        # Single quote
    text = text.replace(":", "\\:")        # Colon
    text = text.replace("%", "\\%")        # Percent
    text = text.replace("{", "\\{")        # Opening curly brace
    text = text.replace("}", "\\}")        # Closing curly brace
    text = text.replace("[", "\\[")        # Opening square bracket
    text = text.replace("]", "\\]")        # Closing square bracket
    text = text.replace(",", "\\,")        # Comma
    text = text.replace(";", "\\;")        # Semicolon
    text = text.replace("\n", "\\n")       # Newline
    text = text.replace("\r", "")          # Remove carriage return
    text = text.replace("\t", " ")         # Tab to space
    
    # Handle other problematic characters
    text = text.replace("|", "\\|")        # Pipe
    text = text.replace("=", "\\=")        # Equals
    text = text.replace("&", "\\&")        # Ampersand
    text = text.replace("@", "\\@")        # At symbol
    text = text.replace("$", "\\$")        # Dollar sign
    text = text.replace("#", "\\#")        # Hash
    text = text.replace("!", "\\!")        # Exclamation
    text = text.replace("?", "\\?")        # Question mark
    text = text.replace("*", "\\*")        # Asterisk
    text = text.replace("+", "\\+")        # Plus
    text = text.replace("(", "\\(")        # Opening parenthesis
    text = text.replace(")", "\\)")        # Closing parenthesis
    text = text.replace("\"", "\\\"")      # Double quote
    text = text.replace("`", "\\`")        # Backtick
    text = text.replace("~", "\\~")        # Tilde
    text = text.replace("^", "\\^")        # Caret
    text = text.replace("<", "\\<")        # Less than
    text = text.replace(">", "\\>")        # Greater than
    text = text.replace("/", "\\/")        # Forward slash
    text = text.replace(".", "\\.")        # Period/Dot
    
    return text


def validate_and_escape_subtitle_text(text):
    """
    Validate subtitle text and escape for FFmpeg.
    
    Args:
        text: Raw text input from user
        
    Returns:
        tuple: (success: bool, result: str, error: str)
    """
    # Check empty
    if not text or not text.strip():
        return False, "", "Subtitle text cannot be empty"
    
    # Check length (reasonable limit)
    if len(text) > 200:
        return False, "", "Subtitle text too long (max 200 characters)"
    
    # Escape all special characters
    escaped_text = escape_subtitle_text(text.strip())
    
    return True, escaped_text, ""


def get_intro_subtitle_filter(intro_settings):
    """
    Generate FFmpeg drawtext filter for hardsub intro subtitle.
    
    Args:
        intro_settings: Dict with subtitle configuration
        
    Returns:
        str: FFmpeg drawtext filter string
    """
    text = intro_settings.get("text", "")
    if not text:
        return ""
    
    # Escape text for FFmpeg
    text = escape_subtitle_text(text)
    
    color = intro_settings.get("color", "white")
    bg_color = intro_settings.get("bg_color", "none")
    duration = intro_settings.get("duration", 5)
    font_size = intro_settings.get("font_size", 24)
    
    # Position: bottom-center (hardcoded)
    # x=(w-text_w)/2 centers horizontally
    # y=h-th-50 places 50px from bottom
    
    bg_filter = ""
    if bg_color != "none":
        # Semi-transparent background box
        bg_filter = f":box=1:boxcolor={bg_color}@0.5:boxborderw=5"
    
    filter_str = (
        f"drawtext=text='{text}':"
        f"fontcolor={color}:"
        f"fontsize={font_size}:"
        f"x=(w-text_w)/2:"
        f"y=h-th-50"
        f"{bg_filter}:"
        f"enable='between(t,0,{duration})'"
    )
    
    return filter_str


def create_subtitle_file(intro_settings, video_path):
    """
    Create SRT subtitle file for softsub intro subtitle.
    
    Args:
        intro_settings: Dict with subtitle configuration
        video_path: Path to video file
        
    Returns:
        str: Path to created SRT file
    """
    text = intro_settings.get("text", "")
    if not text:
        return None
    
    duration = intro_settings.get("duration", 5)
    color = intro_settings.get("color", "white")
    
    # SRT format with styling
    srt_content = f"""1
00:00:00,000 --> 00:00:{duration:02d},000
<font color="{color}">{text}</font>
"""
    
    # Create SRT file with same name as video
    srt_path = video_path.rsplit(".", 1)[0] + ".srt"
    
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    return srt_path


# Color options for UI
COLOR_OPTIONS = {
    "white": "⚪ White",
    "black": "⚫ Black",
    "red": "🔴 Red",
    "blue": "🔵 Blue",
    "yellow": "🟡 Yellow",
    "green": "🟢 Green",
}

# Background color options (includes "none")
BG_COLOR_OPTIONS = {
    "none": "❌ No Background",
    "white": "⚪ White",
    "black": "⚫ Black",
    "red": "🔴 Red",
    "blue": "🔵 Blue",
    "yellow": "🟡 Yellow",
    "green": "🟢 Green",
}
