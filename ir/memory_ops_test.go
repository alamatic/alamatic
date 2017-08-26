package ir

// Assert the interfaces we intend to implement
var _ Value = (*Load)(nil)
var _ Instruction = (*Load)(nil)
var _ Instruction = (*Store)(nil)
