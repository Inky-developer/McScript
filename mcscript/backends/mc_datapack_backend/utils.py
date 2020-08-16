from mcscript.ir.command_components import Position, PositionAxis, PositionKind


def position_to_str(pos: Position) -> str:
    """
    Converts a position to a minecraft position argument

    Args:
        pos: The position

    Returns:
        A position string
    """

    def axis_to_str(axis: PositionAxis) -> str:
        if axis.kind == PositionKind.ABSOLUTE:
            return f"{axis.value}"
        elif axis.kind == PositionKind.RELATIVE:
            return f"~{axis.value}"
        elif axis.kind == PositionKind.LOCAL:
            return f"^{axis.value}"
        raise ValueError(f"Unknown enum variant: {axis.kind}")

    return f"{axis_to_str(pos.x)} {axis_to_str(pos.y)} {axis_to_str(pos.z)}"
