package ir

// Assert the interfaces we intend to implement
var _ Value = (*BinaryOp)(nil)
var _ Instruction = (*BinaryOp)(nil)
