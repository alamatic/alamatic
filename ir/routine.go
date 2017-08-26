package ir

import "github.com/alamatic/alamatic/diag"

// Routine represents the code of a function or process.
type Routine struct {
	declRange *diag.SourceRange

	blocks []*BasicBlock
}

// DeclRange returns a source code range that defines the signature
// of this routine, excluding the routine's body.
func (r *Routine) DeclRange() *diag.SourceRange {
	return r.declRange
}

// Blocks returns a slice of the basic blocks for the routine. The order
// is not significant except that the zeroth element is guaranteed to be
// the entry block.
func (r *Routine) Blocks() []*BasicBlock {
	return r.blocks
}

// EntryBlock returns the routine's entry block.
//
// All well-formed routines have an entry block, but this method may return
// nil for a routine that is still being constructed.
func (r *Routine) EntryBlock() *BasicBlock {
	if len(r.blocks) < 1 {
		return nil
	}
	return r.blocks[0]
}
