# """
# Contains a set of functions that implement common mcfunction commands.
# """
# from __future__ import annotations

# from typing import TYPE_CHECKING

# from mcscript.lang.resource.base.ResourceBase import ValueResource

# if TYPE_CHECKING:
#     from mcscript.compiler.CompileState import CompileState


# def compare_scoreboard_value(_: CompileState, a: ValueResource, relation: Relation,
#                              b: ValueResource) -> ConditionalExecute:
#     """ compares to resources. Tries to optimize if one or both are static"""
#     if a.isStatic and b.isStatic:
#         return ConditionalExecute(relation.testRelation(a.value, b.value))

#     if b.isStatic:
#         a, b = b, a
#         relation = relation.swap()

#     # If any of the two resources is static, we can do a execute if matches
#     if a.isStatic:
#         TestCommand = ExecuteCommand.IF_SCORE_RANGE if relation != Relation.NOT_EQUAL \
#             else ExecuteCommand.UNLESS_SCORE_RANGE
#         return ConditionalExecute(Command.EXECUTE(
#             sub=TestCommand(
#                 stack=b.value,
#                 range=relation.swap().getRange(a.value)
#             )
#         ))

#     TestCommand = ExecuteCommand.IF_SCORE if relation != relation.NOT_EQUAL else ExecuteCommand.UNLESS_SCORE
#     return ConditionalExecute(Command.EXECUTE(
#         sub=TestCommand(
#             stack=a.value,
#             relation=relation.value if relation != relation.NOT_EQUAL else Relation.EQUAL.value,
#             stack2=b.value
#         )
#     ))
