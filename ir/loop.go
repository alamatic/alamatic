package ir

type Loop struct {
	Routine *Routine

	// Header is the earliest point to which control returns on subsequent
	// iterations of the loop.
	Header *BasicBlock

	// Body is the set of basic blocks that belong to the body of the
	// loop. A given block may be a member of multiple loops where loops
	// are nested.
	//
	// This map represents a set, so the only value allowed is "true".
	Body map[*BasicBlock]bool

	// Parent is the loop that this loop is nested directly within, if any.
	// Will be nil if this is a top-level loop.
	Parent *Loop
}

func (loop *Loop) NewChild() *Loop {
	childLoop := loop.Routine.NewLoop()
	childLoop.Parent = loop
	return childLoop
}
