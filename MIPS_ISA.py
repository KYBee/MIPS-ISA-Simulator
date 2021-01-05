# MIPS ISA Processor
class Processor:
    R_format = ["ADD", "OR"]
    I_format = ["ADDI", "ORI"]
    I_memory = ["SW", "LW"]

    def __init__(self, Instructions):
        # 4 Pipeline Register
        self.Pipelines = [IFIDRegister(), IDEXRegister(), EXMEMRegister(), MEMWBRegister()]

        # IFID Register에 Instruction을 Fetching 하기 위해 IFIDRegister 클래스로 NextInstruction 선언
        self.NextInstruction = IFIDRegister()

        # InstructionMemory Which Contains All Instructions
        self.InstructionMemory = Instructions
        self.InstructionCount = len(Instructions)

        #Forward Unit
        self.ForwardA = '00'
        self.ForwardB = '00'

        #Load Use Data Hazard Unit
        self.PCWrite = '1'
        self.IFIDWrite = '1'
        self.IDEXFlush = '0'

        self.Trial = 0
        self.ClockCount = len(Instructions) - 1 + 5
    
    def Initialize(self):
        self.ForwardA = '00'
        self.ForwardB = '00'

    def MUX(self, a, b, code):
        return b if code else a

    # Fetching Instruction
    def Fetch(self, IF=None):
        # Empty Instruction For None Instruction     
        if IF == None:
            self.NextInstruction.OPcode = None
            self.NextInstruction.registerRs = '0'
            self.NextInstruction.registerRt = '0'
            self.NextInstruction.registerRd = '0'
        # Instruction with R-format
        elif IF[0] in self.R_format:
            self.NextInstruction.OPcode = IF[0]
            self.NextInstruction.registerRs = IF[2]
            self.NextInstruction.registerRt = IF[3]
            self.NextInstruction.registerRd = IF[1]
        # Instruction with I-format
        elif IF[0] in self.I_memory + self.I_format:
            self.NextInstruction.OPcode = IF[0]
            self.NextInstruction.registerRs = IF[2]
            self.NextInstruction.registerRt = IF[1]
            self.NextInstruction.registerRd = '0'

    # Deciding Control Signal in ID stage
    def ControlUnit(self, reg):
        #returning regWrtie, memRead
        if reg.OPcode == None:
            return ('0', '0')
        elif reg.OPcode in Processor.R_format:
            return ('1', '0')
        elif reg.OPcode in Processor.I_format:
            return ('1', '0')
        elif reg.OPcode == "LW":
            return ('1', '1')
        elif reg.OPcode == "SW":
            return ('0', '0')

    # Detecting Forward Unit
    def ForwardUnit(self):
        IDEX, EXMEM, MEMWB = self.Pipelines[1], self.Pipelines[2], self.Pipelines[3]

        # Forward A
        if EXMEM.regWrite == '1' and EXMEM.registerRd == IDEX.registerRs and EXMEM.registerRd != '0':
            self.ForwardA = "10"
        elif MEMWB.regWrite == '1' and MEMWB.registerRd == IDEX.registerRs and MEMWB.registerRd != '0':
            self.ForwardA = "01"
        else:
            self.ForwardA = "00"

        # Forward B
        if EXMEM.regWrite == '1' and EXMEM.registerRd == IDEX.registerRt and EXMEM.registerRd != '0':
            self.ForwardB = "10"
        elif MEMWB.regWrite == '1' and MEMWB.registerRd == IDEX.registerRt and MEMWB.registerRd != '0':
            self.ForwardB = "01"
        else:
            self.ForwardB = "00"

    # Flushing
    def Flush(self, reg):
        reg.registerRs = '0'
        reg.registerRt = '0'
        reg.registerRd = '0'
        reg.regWrite = '0'
        reg.memRead = '0'
        reg.RegDst = '0'
        return reg

    # Detecting Load Use Data Hazard
    def HazardDetectionUnit(self):
        IDEX, IFID = self.Pipelines[1], self.Pipelines[0]
        if IDEX.memRead == '1' and (IDEX.registerRt == IFID.registerRs or IDEX.registerRt == IFID.registerRt):
            return ('0', '0', '1')
        else:
            return ('1', '1', '0')

    # Clock Cycle
    def Clock(self, IF=None):
        self.Fetch(IF)
        self.Initialize()
        reg = self.Pipelines

        # Execute Flush
        if self.IDEXFlush == '1':
            self.PCWrite = '1'
            self.IFIDWrite = '1'
            self.IDEXFlush = '0'
            reg[3].regWrite, reg[3].memRead, reg[3].registerRd = reg[2].regWrite, reg[2].memRead, reg[2].registerRd
            reg[2].regWrite, reg[2].memRead = reg[1].regWrite, reg[1].memRead
            # Deciding RegDst
            reg[2].registerRd = self.MUX(reg[1].registerRd, reg[1].registerRt, reg[1].RegDst == "0")
            # Flushing
            reg[1] = self.Flush(reg[1])
            self.ClockCount += 1
            self.Pipelines = reg
            return

        # Send Info to Next Level Register
        reg[3].regWrite, reg[3].memRead, reg[3].registerRd = reg[2].regWrite, reg[2].memRead, reg[2].registerRd
        reg[2].regWrite, reg[2].memRead = reg[1].regWrite, reg[1].memRead
        # Deciding RegDst
        reg[2].registerRd = self.MUX(reg[1].registerRd, reg[1].registerRt, reg[1].RegDst == "0")
        # Deciding Control Unit Code
        reg[1].regWrite, reg[1].memRead = self.ControlUnit(reg[0])
        reg[1].registerRs, reg[1].registerRt, reg[1].registerRd = reg[0].registerRs, reg[0].registerRt, reg[0].registerRd
        # Deciding RegDst Control Signal
        reg[1].RegDst = '1' if reg[0].registerRd != '0' else '0'
        reg[0].OPcode, reg[0].registerRd = self.NextInstruction.OPcode, self.NextInstruction.registerRd
        reg[0].registerRs, reg[0].registerRt = self.NextInstruction.registerRs, self.NextInstruction.registerRt

        # Detecting Load Use Data Hazard
        self.PCWrite, self.IFIDWrite, self.IDEXFlush = self.HazardDetectionUnit()

        # Detection Data Hazard
        self.ForwardUnit()

        self.Pipelines = reg
        self.Trial += 1



# Pipeline Register Class
class Register:
    regWrite = '0'
    memRead = '0'

# IF/ID Register
class IFIDRegister():
    def __init__(self):
        self.OPcode = None
        self.registerRs = '0'
        self.registerRt = '0'
        self.registerRd = '0'

# ID/EX Register
class IDEXRegister(Register):
    def __init__(self):
        self.registerRs = '0'
        self.registerRt = '0'
        self.registerRd = '0'
        # Register Destination which would be send to EX/MEM Register
        # output of MUX(RegDst, RegisterRt)
        self.RegDst = '0'

# EX/MEM Regitser
class EXMEMRegister(Register):
    def __init__(self):
        self.registerRd = '0'

# MEM/WB Register
class MEMWBRegister(Register):
    def __init__(self):
        self.registerRd = '0'