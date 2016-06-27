package ir

import (
	"bytes"
	"fmt"
	"io"
)

func DebugRoutineBody(r *Routine, f io.Writer) {
	type instrId struct {
		blockIdx int
		instrIdx int
	}
	blockIdx := map[*BasicBlock]int{}
	instrIds := map[Instruction]instrId{}

	blocks := r.BasicBlocks()
	for bi, block := range blocks {
		blockIdx[block] = bi
		for ii, instr := range block.Instructions {
			instrIds[instr] = instrId{bi, ii + 1}
		}
		if term := block.Terminator; term != nil {
			instrIds[term] = instrId{bi, len(block.Instructions) + 1}
		}
	}

	literalStr := func(l *Literal) string {
		if l == Void {
			return "void"
		}

		if l == True {
			return "true"
		}

		if l == False {
			return "false"
		}

		// Shouldn't get here once this function is complete
		return "<unprintable-constant>"
	}

	printValue := func(val Value) {
		if instr, ok := val.(Instruction); ok {
			id := instrIds[instr]
			fmt.Fprintf(f, "%%%02d:%02d", id.blockIdx, id.instrIdx)
		} else if block, ok := val.(*BasicBlock); ok {
			idx := blockIdx[block]
			fmt.Fprintf(f, "block%02d", idx)
		} else if lit, ok := val.(*Literal); ok {
			fmt.Fprintf(f, "%s", literalStr(lit))
		} else {
			// Shouldn't get here once this function is actually complete
			fmt.Fprintf(f, "???")
		}
	}

	printInstr := func(instr Instruction) {
		id := instrIds[instr]
		fmt.Fprintf(f, "    %%%02d:%02d = %s", id.blockIdx, id.instrIdx, instr.Mnemonic())
		if arger, ok := instr.(Argumenter); ok {
			args := arger.Arguments()
			first := true
			for _, arg := range args {
				if first {
					fmt.Fprintf(f, " ")
					first = false
				} else {
					fmt.Fprintf(f, ", ")
				}
				printValue(arg)
			}
		}
		fmt.Fprintf(f, "\n")
	}

	for i, block := range blocks {
		fmt.Fprintf(f, "block%02d:\n", i)
		for _, instr := range block.Instructions {
			printInstr(instr)
		}
		if block.Terminator != nil {
			printInstr(block.Terminator)
		}
		fmt.Fprintf(f, "\n")
	}
}

func DebugRoutineBodyStr(r *Routine) string {
	buf := &bytes.Buffer{}
	DebugRoutineBody(r, buf)
	return buf.String()
}
