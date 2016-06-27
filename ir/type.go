package ir

import (
//"llvm.org/llvm/bindings/go/llvm"
)

type Type struct {
	//LLVMType llvm.Type
}

// VoidType is a type representing the absense of a value.
var VoidType = &Type{ /*llvm.VoidType()*/ }

// BoolType is the boolean type
var BoolType = &Type{ /*llvm.Int1Type()*/ }
