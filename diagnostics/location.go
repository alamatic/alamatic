package diagnostics

type SourceLocation struct {
	Filename string
	Line     int
	Column   int
}

type SourceRange struct {
	Start SourceLocation
	End   SourceLocation
}
