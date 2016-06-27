package ir

import (
	"testing"
)

func TestBuilderBasics(t *testing.T) {
	routine := NewRoutine()
	entryBuilder := routine.Entry.NewBuilder()
	secondBuilder := entryBuilder.NewBasicBlock().NewBuilder()
	entryBuilder.Jump(secondBuilder.Block)
	secondBuilder.Return(True)

	got := routine.BodyStr()
	expected := `block00:
    %00:01 = jump block01

block01:
    %01:01 = return true

`
	if got != expected {
		t.Fatalf("incorrect body\n--- got... ---\n%s\n--- want... ---\n%s\n", got, expected)
	}
}
