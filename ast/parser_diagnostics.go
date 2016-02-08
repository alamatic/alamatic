package ast

import (
	"github.com/alamatic/alamatic/diag"
)

type InconsistentIndentation struct {
	diag.Message `Inconsistent indentation`
}

type NewlineExpected struct {
	diag.Message `End of line expected`
}
