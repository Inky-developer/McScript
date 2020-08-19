scoreboard players set .exp2_0 mcscript 1
scoreboard players set .exp2_1 mcscript 0
scoreboard players set .exp7_2 mcscript 0
execute unless score .exp2_0 mcscript matches 0 if score .exp2_1 mcscript matches 0 run scoreboard players set .exp7_2 mcscript 1
execute if score .exp2_0 mcscript matches 0 unless score .exp2_1 mcscript matches 0 run scoreboard players set .exp7_2 mcscript 1
scoreboard players set .exp8_2 mcscript 0
execute unless score .exp2_1 mcscript matches 0 if score .exp2_0 mcscript matches 0 run scoreboard players set .exp8_2 mcscript 1
execute if score .exp2_1 mcscript matches 0 unless score .exp2_0 mcscript matches 0 run scoreboard players set .exp8_2 mcscript 1
scoreboard players set .exp9_2 mcscript 0
execute unless score .exp2_0 mcscript matches 0 if score .exp2_0 mcscript matches 0 run scoreboard players set .exp9_2 mcscript 1
execute if score .exp2_0 mcscript matches 0 unless score .exp2_0 mcscript matches 0 run scoreboard players set .exp9_2 mcscript 1
scoreboard players set .exp10_2 mcscript 0
execute unless score .exp2_1 mcscript matches 0 if score .exp2_1 mcscript matches 0 run scoreboard players set .exp10_2 mcscript 1
execute if score .exp2_1 mcscript matches 0 unless score .exp2_1 mcscript matches 0 run scoreboard players set .exp10_2 mcscript 1
scoreboard players set .exp2_2 mcscript 0
execute unless score .exp7_2 mcscript matches 0 unless score .exp8_2 mcscript matches 0 if score .exp9_2 mcscript matches 0 if score .exp10_2 mcscript matches 0 run scoreboard players set .exp2_2 mcscript 1
scoreboard players set .exp2_3 mcscript 0
execute unless score .exp2_2 mcscript matches 0 run scoreboard players set .exp2_3 mcscript 1
scoreboard players operation result mcscript_test = .exp2_3 mcscript
tellraw @a [{"text": "The test result is: "}, {"score": {"name": "result", "objective": "mcscript_test"}}]
