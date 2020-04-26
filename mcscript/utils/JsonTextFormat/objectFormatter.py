from typing import Dict

from mcscript.data import commands
from mcscript.utils.utils import requiresMcVersion


def format_text(text: str) -> Dict:
    return {"text": text}


def format_score(scoreboard: str, player: str) -> Dict:
    return {
        "score": {
            "name"     : player,
            "objective": scoreboard
        }
    }


def format_nbt(storage: str, nbt: str) -> Dict:
    return {
        "nbt"    : f"{commands.Storage.VARS.value}.{nbt}",
        "storage": storage
    }


def format_selector(selector: str) -> Dict:
    return {
        "selector": selector
    }


def format_bold(data: Dict) -> Dict:
    return {**data, "bold": "true"}


def format_italic(data: Dict) -> Dict:
    return {**data, "italic": "true"}


def format_strike_through(data: Dict) -> Dict:
    return {**data, "strikethrough": "true"}


def format_underlined(data: Dict) -> Dict:
    return {**data, "underlined": "true"}


def format_obfuscated(data: Dict) -> Dict:
    return {**data, "obfuscated": "true"}


def format_color(data: Dict, color: str) -> Dict:
    if color.startswith("#"):
        return _format_hex_color(data, color)
    return {**data, "color": color}


@requiresMcVersion(2529, "Support for hexadecimal color values was added in 1.16 (20w17a)")
def _format_hex_color(data: Dict, color: str) -> Dict:
    if len(color) != 7:
        raise ValueError(f"Required hexadecimal string of format #rrggbb but got {color}")
    for i in range(1, 7, 2):
        try:
            int(color[i:i + 2], 16)
        except ValueError:
            raise ValueError(f"Required hexadecimal string of format #rrggbb but got {color}") from None

    return {**data, "color": color}
