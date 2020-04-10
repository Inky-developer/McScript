import re


class DataReader:
    pattern_key = re.compile(r"\[(\w+)\]$")

    def __init__(self):
        pass

    def read(self, text):
        ret = {}

        key = None
        value = []
        for index, line in enumerate(text.split("\n")):
            if not line and key is None:
                continue
            if not (match := self.pattern_key.match(line)) and key is None:
                raise ValueError(f"Invalid key at line {index + 1}")
            elif match:
                if key:
                    if key not in ret:
                        ret[key] = []
                    ret[key].append("\n".join(value).strip())
                    value = []
                key = match.group(1)
            elif key is not None:
                value.append(line)
            else:
                key = match.group(1)
        if key:
            if key not in ret:
                ret[key] = []
            ret[key].append("\n".join(value).strip())

        return ret
