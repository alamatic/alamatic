package ir

type Loop struct {
	routine *Routine

	header *BasicBlock

	// Body is the set of basic blocks that belong to the body of the
	// loop. A given block may be a member of multiple loops where loops
	// are nested.
	//
	// This map represents a set, so the only value allowed is "true".
	body map[*BasicBlock]struct{}

	parent *Loop
}

/*func (l *Loop) NewChild() *Loop {
	childLoop := l.Routine.NewLoop()
	childLoop.Parent = l
	return childLoop
}*/

// Parent returns the loop that this loop is nested directly within, if any.
// Returns nil if this is a top-level loop.
func (l *Loop) Parent() *Loop {
	return l.parent
}

func (l *Loop) Routine() *Routine {
	return l.routine
}

// Header returns the earliest point to which control returns on subsequent
// iterations of the loop.
func (l *Loop) Header() *BasicBlock {
	return l.header
}

// Blocks appends to the given slice (which may be nil) pointers to all of
// the basic blocks that form the loop body.
//
// A given block may be a member of multiple loops when loops are nested.
func (l *Loop) Blocks(target []*BasicBlock) []*BasicBlock {
	for block := range l.body {
		target = append(target, block)
	}
	return target
}
