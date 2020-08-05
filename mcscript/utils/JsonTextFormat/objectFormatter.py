from typing import Dict

from mcscript.utils.resources import ScoreboardValue, DataPath
from mcscript.utils.utils import requiresMcVersion


def format_text(text: str) -> Dict:
    return {"text": text}


def format_score(scoreboard_value: ScoreboardValue) -> Dict:
    return {
        "score": {
            "name": scoreboard_value.value,
            "objective": scoreboard_value.scoreboard.unique_name
        }
    }


def format_nbt(path: DataPath, interpret: bool = False) -> Dict:
    ret = {
        "nbt": f"{path.dotted_path()}",
        "storage": f"{path.storage}"
    }
    if interpret:
        ret["interpret"] = True

    return ret


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


def format_open_url(data: Dict, url: str) -> Dict:
    if "clickEvent" in data:
        raise ValueError(f"Cannot create click event for url '{url}' because there already is a click event "
                         f"({data['clickEvent']['value']})")
    return {
        **data,
        "clickEvent": {
            "action": "open_url",
            "value": url
        }
    }


def format_run_command(data: Dict, command: str) -> Dict:
    if "clickEvent" in data:
        raise ValueError(f"Cannot create click event to run command '{command}' because there already is a click event "
                         f"({data['clickEvent']['value']})")
    if len(command) >= 100:
        raise ValueError(f"Due to a limitation of minecraft the maximum command length is 100 characters, "
                         f"got {len(command)}")

    return {
        **data,
        "clickEvent": {
            "action": "run_command",
            "value": command
        }
    }


def format_hover(data: Dict, hover_text: str) -> Dict:
    # sadly it does not seem like minecraft supports selectors as hover text
    # ToDo: test if scores and nbt work
    return {
        **data,
        "hoverEvent": {
            "action": "show_text",
            "value": hover_text
        }
    }


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
