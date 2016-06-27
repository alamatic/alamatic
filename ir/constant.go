package ir

import (
//"llvm.org/llvm/bindings/go/llvm"
)

type Literal struct {
	TypedValue
}

// Void is a literal that acts as the only instance of VoidType.
//
// This can be returned as the result of instructions that produce no value.
// There is no way to directly represent void in the Alamatic source language,
// but this value may be produced during lowering to IR or during type
// analysis.
var Void = &Literal{
	TypedValue{
		Type: VoidType,
		//Value: nil,
	},
}

// True is a literal BoolType representing boolean true.
var True = &Literal{
	TypedValue{
		Type: BoolType,
		//Value: llvm.ConstInt(llvm.Int1Type(), 1, false),
	},
}

// False is a literal BoolType representing boolean false.
var False = &Literal{
	TypedValue{
		Type: BoolType,
		//Value: llvm.ConstInt(llvm.Int1Type(), 0, false),
	},
}
