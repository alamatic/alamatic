package ir

import (
	"testing"
)

type testInst struct {
	mnemonic "test"

	operands []Value
}

func (i *testInst) Operands() []Value {
	return i.operands
}

type testInstNoMnemonic struct{}

func (i *testInstNoMnemonic) Operands() []Value {
	return nil
}

func TestInstructionMnemonic(t *testing.T) {
	inst := &testInst{}

	got := InstructionMnemonic(inst)
	if expected := "test"; got != expected {
		t.Errorf("Wrong mnemonic %#v; want %#v", got, expected)
	}

	instNoMnem := &testInstNoMnemonic{}

	got = InstructionMnemonic(instNoMnem)
	if expected := ""; got != expected {
		t.Errorf("Wrong mnemonic %#v; want %#v", got, expected)
	}
}
