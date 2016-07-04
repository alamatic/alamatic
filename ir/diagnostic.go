package ir

import (
	"github.com/alamatic/alamatic/diag"
)

// DiagnosticOp is a funny sort of instruction that is used to represent
// diagnostics (i.e. errors and warnings). It doesn't represent any actual
// runtime behavior, but rather will cause compilation to fail if it remains
// in the IR after analysis.
type DiagnosticOp struct {
	Diagnostics []*diag.Diagnostic
}

func (i *DiagnosticOp) Mnemonic() string {
	return "diag"
}

func (i *DiagnosticOp) Arguments() []Value {
	return []Value{}
}
