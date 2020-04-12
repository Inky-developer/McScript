# 2**24-1, max tick length ~ 30s
gamerule maxCommandChainLength 16777215
scoreboard objectives remove McScript
scoreboard objectives add McScript dummy

data remove storage McScript:main state

scoreboard objectives setdisplay sidebar mcscript
tellraw @a ["", {"text": "["}, {"text":"McScript", "color":"gold", "clickEvent":{"action":"suggest_command", "value":"/function McScript:main"}, "hoverEvent":{"action":"show_text","value":"click to run"}}, {"text":"] loaded"}]

function McScript:main