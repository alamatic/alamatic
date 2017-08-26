package ir

import (
	"github.com/alamatic/alamatic/diag"
)

// Local represents a local variable within a routine.
//
// Locals are conventionally allocated on the stack and are thus invalidated
// once their associated function returns.
type Local struct {
	declRange *diag.SourceRange
	routine   *Routine
	value
}

func (l *Local) Routine() *Routine {
	return l.routine
}

func (l *Local) SourceRange() *diag.SourceRange {
	return l.declRange
}

func (l *Local) DeclRange() *diag.SourceRange {
	return l.declRange
}
