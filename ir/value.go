package ir

type Value interface {
}

type Argumenter interface {
	Arguments() []Value
}

type TypedValue struct {
	Type *Type
	//Value *llvm.Value
}
