package ir

type Routine struct {
	// Entry is the first basic block that will execute when the
	// routine begins.
	//
	// This block serves as the "root" of the control flow graph,
	// with the rest of the graph described by the terminator of this
	// and other blocks in the graph.
	Entry *BasicBlock

	// PosParams contains the subset of parameters that can be passed
	// values positionally, indexed by their position.
	PosParams []*Parameter

	// NamedParams contains the subset of parameters that can be passed
	// values by name, indexed by that name.
	// Some parameters may appear both in PosParams and NamedParams, but
	// it is illegal for a single call to use both methods to fill the
	// same parameter.
	NamedParams map[string]*Parameter

	// PosCollectorParam is a special parameter that "collects" all remaining
	// positional parameters that do not correspond to parameters in PosParams,
	// as a tuple that can be indexed by constant integers.
	PosCollectorParam *Parameter

	// NamedCollectorParam is a special parameter that "collects" all
	// remaining named parameters that do not correspond to parameters in
	// NamedParams, as a mapping that can be indexed by constant strings.
	NamedCollectorParam *Parameter
}

type Parameter struct {
}

func NewRoutine() *Routine {
	r := &Routine{}
	r.Entry = r.NewBasicBlock()
	return r
}

func (r *Routine) NewBasicBlock() *BasicBlock {
	return &BasicBlock{
		Routine:      r,
		Instructions: []Instruction{},
		Terminator:   nil,
	}
}

func (r *Routine) NewLoop() *Loop {
	loop := &Loop{}

	loop.Header = r.NewBasicBlock()
	loop.Header.Loop = loop

	loop.Body = map[*BasicBlock]bool{}

	return loop
}

// BasicBlocks returns a slice of all of the basic blocks in this routine
// in a predictable order where predecessors appear before their successors
// unless a loop is present, and where a loop is present the result is
// deterministic with each block appearing exactly once.
//
// Unreachable blocks are not included in the result, due to how this
// function traverses the control flow graph.
func (r *Routine) BasicBlocks() []*BasicBlock {
	emitted := map[*BasicBlock]bool{}
	blockStack := []*BasicBlock{}
	blocks := []*BasicBlock{}

	current := r.Entry
	for current != nil {
		blocks = append(blocks, current)
		emitted[current] = true

		blockStack = append(blockStack, current.Successors()...)

		for {
			if len(blockStack) > 0 {
				current = blockStack[len(blockStack)-1]
				blockStack = blockStack[:len(blockStack)-1]
				if !emitted[current] {
					break
				}
			} else {
				current = nil
				break
			}
		}
	}

	return blocks
}
