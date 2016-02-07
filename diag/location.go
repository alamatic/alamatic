package diag

// SourceLocation represents a particular character in a provided source file.
type SourceLocation struct {
	Filename string
	Line     int
	Column   int
}

// SourceRange represents a range of characters in a provided source file,
// described by a start and end SourceLocation that are both inclusive.
//
// In principle each of these SourceLocation objects could have different
// Filename values, but in practice this cannot arise due to the parsing model
// and so callers are free to assume that the two locations are always in the
// same file.
type SourceRange struct {
	Start SourceLocation
	End   SourceLocation
}
