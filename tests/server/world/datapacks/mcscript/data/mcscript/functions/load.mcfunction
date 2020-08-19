scoreboard objectives remove mcscript
scoreboard objectives add mcscript dummy
scoreboard objectives remove mcscript_test
scoreboard objectives add mcscript_test dummy
scoreboard objectives setdisplay sidebar mcscript
tellraw @a [{"text": "["}, {"text": "mcscript", "color": "gold"}, {"text": "] loaded!"}]
function mcscript:main
