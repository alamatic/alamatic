package diag

import (
	"fmt"
)

type Level int

const (
	_ = Level(iota)
	Warning
	Error
)

func (l Level) String() string {
	switch l {
	case Warning:
		return "WARNING"
	case Error:
		return "ERROR"
	default:
		// Should never happen
		panic(fmt.Errorf("Invalid diagnostic level %v", l))
	}
}
