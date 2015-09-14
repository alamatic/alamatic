package ir

import (
	"reflect"
)

type Instruction interface {
	Operands() []Value
}

type ValueInstruction interface {
	Value
	Instruction
}

// mnemonic is an empty struct designed to be embedded into an
// implementer of Instruction and tagged with a mnemonic for the
// instruction that can be helpful for inclusion in debug-oriented
// output. Instruction mnemonics are not used in the normal path of
// the compiler since IR is an in-memory format only, not intended
// for the consumption of an end-user.
//
// For example:
//    type someInst struct {
//        mnemonic "something"
//    }
type mnemonic struct{}

var mnemonicType = reflect.TypeOf(mnemonic{})

// InstructionMnemonic extracts and returns the type mnemonic for an
// instruction, assuming it has one. Instruction mnemonics are for
// debugging use-cases only and should not be used in the normal case
// of the program.
// If the given instruction has no mnemonic then the empty string is
// returned.
func InstructionMnemonic(i Instruction) string {
	iType := reflect.TypeOf(i).Elem()
	field, ok := iType.FieldByName("mnemonic")
	if !ok {
		return ""
	}

	if field.Type != mnemonicType {
		// Apparently this instruction has a "mnemonic" member that
		// *isn't* a mnemonic tag.
		return ""
	}

	return string(field.Tag)
}
