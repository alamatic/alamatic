package ir

import (
	"testing"
)

func TestBuilderBasics(t *testing.T) {
	routine := NewRoutine()
	entryBuilder := routine.Entry.NewBuilder()
	secondBuilder := entryBuilder.NewBasicBlock()
	entryBuilder.Jump(secondBuilder.Block)
	result := secondBuilder.Equals(True, True)
	secondBuilder.Return(result)

	got := routine.BodyStr()
	expected := `block00:
    %00:01 = jump block01

block01:
    %01:01 = equals true, true
    %01:02 = return %01:01

`
	if got != expected {
		t.Fatalf("incorrect body\n--- got... ---\n%s\n--- want... ---\n%s\n", got, expected)
	}
}

func TestBuilderLoops(t *testing.T) {
	routine := NewRoutine()

	builders := make([]*Builder, 8)
	builders[0] = routine.Entry.NewBuilder()
	builders[1] = builders[0].NewBasicBlock()
	builders[2] = builders[1].NewLoop()
	builders[3] = builders[2].NewBasicBlock()
	builders[4] = builders[3].NewLoop()
	builders[5] = builders[4].NewBasicBlock()
	builders[6] = builders[3].NewBasicBlock()
	builders[7] = builders[1].NewBasicBlock()

	builders[0].Jump(builders[1].Block)
	builders[1].Jump(builders[2].Block)
	builders[2].Jump(builders[3].Block)
	builders[3].Jump(builders[4].Block)
	builders[4].Jump(builders[5].Block)
	builders[5].Branch(True, builders[4].Block, builders[6].Block)
	builders[6].Branch(True, builders[2].Block, builders[7].Block)
	builders[7].Return(Void)

	got := routine.BodyStr()
	expected := `block00:
    %00:01 = jump block01

block01:
    %01:01 = jump block02

block02:
    %02:01 = jump block03

block03:
    %03:01 = jump block04

block04:
    %04:01 = jump block05

block05:
    %05:01 = branch true, block04, block06

block06:
    %06:01 = branch true, block02, block07

block07:
    %07:01 = return void

`

	if got != expected {
		t.Fatalf("incorrect body\n--- got... ---\n%s\n--- want... ---\n%s\n", got, expected)
	}

	if builders[0].Block.Loop != nil {
		t.Fatalf("block 0 in loop %#v; want nil", builders[0].Block.Loop)
	}
	if builders[1].Block.Loop != nil {
		t.Fatalf("block 1 in loop %#v; want nil", builders[1].Block.Loop)
	}
	if builders[7].Block.Loop != nil {
		t.Fatalf("block 7 in loop %#v; want nil", builders[7].Block.Loop)
	}
	block0loops := builders[0].Block.AllLoops()
	if len(block0loops) != 0 {
		t.Fatalf("block 0 has %d loops; want 0", len(block0loops))
	}

	if builders[2].Block.Loop == nil {
		t.Fatalf("block 2 in loop nil; want an actual loop")
	}
	loop0 := builders[2].Block.Loop
	if builders[3].Block.Loop != loop0 {
		t.Fatalf("block 3 in loop %#v; want %#v", builders[3].Block.Loop, loop0)
	}
	if builders[6].Block.Loop != loop0 {
		t.Fatalf("block 6 in loop %#v; want %#v", builders[6].Block.Loop, loop0)
	}
	block2loops := builders[2].Block.AllLoops()
	if len(block2loops) != 1 {
		t.Fatalf("block 2 has %d loops; want 1", len(block0loops))
	}
	if block2loops[0] != loop0 {
		t.Fatalf("block 2 has loops %#v; want slice with just %#v", block2loops, loop0)
	}

	if builders[4].Block.Loop == nil {
		t.Fatalf("block 4 in loop nil; want an actual loop")
	}
	loop1 := builders[4].Block.Loop
	if loop1 == loop0 {
		t.Fatalf("block 4 is in the same loop as block 2; want different loops")
	}
	if builders[5].Block.Loop != loop1 {
		t.Fatalf("block 5 in loop %#v; want %#v", builders[5].Block.Loop, loop1)
	}
	block4loops := builders[4].Block.AllLoops()
	if len(block4loops) != 2 {
		t.Fatalf("block 4 has %d loops; want 2", len(block4loops))
	}
	if block4loops[0] != loop1 {
		t.Fatalf("block4loops[0] == %#v; want %#v", block4loops[0], loop1)
	}
	if block4loops[1] != loop0 {
		t.Fatalf("block4loops[1] == %#v; want %#v", block4loops[1], loop0)
	}
}
