// Package ir contains types used in the first internal representation of
// Alamatic code, after lowering from the AST.
//
// In the compilation pipeline, Alamatic IR is built from Alamatic AST and
// is eventually lowered into LLVM IR. Alamatic IR does not carry type
// information, but is used for the type tracing/inference pass along with
// other semantic analyses of the program.
//
// The intended division of responsibility is that Alamatic IR is used for
// analysis and implementation of language semantics, while LLVM IR is used
// only for optimizations that do not affect the behavior or semantics. Some
// of the work done using Alamatic IR is traditionally thought of as
// optimization (constant propagation, dead code elimination) but in Alamatic
// these operations have a user-visible effect on the interpretation of the
// code.
//
// Alamatic IR is in SSA form, though at this level of abstraction "registers"
// are used only for temporary results within expressions since memory accesses
// have not yet been lowered.
package ir
