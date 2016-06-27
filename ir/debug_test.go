package ir

// Note that this is wrappers around the debug utilities that are more
// convenient for testing, as opposed to tests of the debug utilities
// themselves.

func (r *Routine) BodyStr() string {
	return DebugRoutineBodyStr(r)
}
