from MIPS_ISA import *
import pandas as pd
import sys

# Reading Input File
def ReadCode(fname):
    try:
        f = open(fname, "r")
    except IOError:
        print("File not exist. Check file name")
        exit(1)

    lines = f.readlines()
    f.close()

    return lines, fname


# Writing Simulation
def WriteSimulation(processor, registers):
    CC = []
    CC.append(registers[0].registerRs)
    CC.append(registers[0].registerRt)
    CC.append(registers[0].registerRd)

    CC.append(registers[1].registerRs)
    CC.append(registers[1].registerRt)
    CC.append(registers[1].registerRd)
    CC.append(registers[1].regWrite)
    CC.append(registers[1].memRead)
    CC.append(registers[1].RegDst)

    CC.append(registers[2].registerRd)
    CC.append(registers[2].regWrite)

    CC.append(registers[3].registerRd)
    CC.append(registers[3].regWrite)

    CC.append(processor.ForwardA)
    CC.append(processor.ForwardB)
    CC.append(processor.PCWrite)
    CC.append(processor.IFIDWrite)
    CC.append(processor.IDEXFlush)
    
    return CC

# DataFrame Index
df_index = ["IF/ID.registerRs", "IF/ID.registerRt", "IF/ID.registerRd",
            "ID/EX.registerRs", "ID/EX.registerRt", "ID/EX.registerRd", "ID/EX.regWrite", "ID/EX.memRead", "ID/EX.RegDst",
            "EX/MEM.registerRd", "EX/MEM.regWrite",
            "MEM/WB.registerRd", "MEM/WB.regWrite",
            "ForwardA", "ForwardB", "PC.Write", "IF/ID.Write", "ID/EX.Flush"]

# Making Empty DataFrame
output = pd.DataFrame([], index=df_index)



# Loading Instructions
if len(sys.argv) <= 1:
    fname = input("Enter File Name: ")
    instructions, fname = ReadCode(fname)
else:
    instructions, fname = ReadCode(sys.argv[1])
Instructions = []

for instruction in instructions:
    instruction = instruction.strip().split(" ")

    if instruction[0] in Processor.I_memory:
        offset, rt = tuple(instruction[-1].split("("))
        instruction[-1:] = [rt, offset]
   
    for i in range(len(instruction)):
        instruction[i] = instruction[i].strip(",$)")

    Instructions.append(instruction)

# Loading Processor
MIPS = Processor(Instructions)




# Running Assembly Code
trial = 0 
while trial < MIPS.ClockCount:

    # Recording Each Clock Cycle's Status in DataFrame
    simulation = WriteSimulation(MIPS, MIPS.Pipelines)
    k = pd.Series(simulation, name="CC" + str(trial + 1), index=df_index)
    output = pd.concat([output, k], axis=1)
    
    # Clock Cycle
    if MIPS.InstructionCount > MIPS.Trial:
        MIPS.Clock(MIPS.InstructionMemory[MIPS.Trial])
    else:
        MIPS.Clock()

    trial += 1

# Showing Output in Console
print("Simulation Result")
print(output)

# Extracting Output DataFrame to CSV File
fname = fname.split(".")[0]
output.to_csv(fname + "_output.csv", encoding="utf-8")