package tokenizer

import (
	"fmt"

	"github.com/alamatic/alamatic/diagnostics"
)

// Tokenize is the main entry point to the tokenizer.
//
// It takes a byte slice of the source code along with the filename where
// it came from and returns an unbuffered channel that yields the logical
// tokens found in the stream.
func Tokenize(data []byte, filename string) <-chan Token {
	rawChan := Scan(data, filename)
	return RaiseRawTokens(rawChan)
}

// RaiseRawTokens takes a channel of raw tokens and produces a new channel
// of the corresponding logical tokens.
//
// Most callers should use Tokenize, which wraps this function to produce
// logical tokens directly from source.
func RaiseRawTokens(rawChan <-chan Token) <-chan Token {
	logChan := make(chan Token)

	go func() {
		bracketCount := 0
		indents := make([]int, 0, 20)
		startOfLine := true

		indents = append(indents, 0)

		outdentTo := func(newIndent int, loc *diagnostics.SourceLocation) {
			for {
				currentIndent := indents[len(indents)-1]
				if newIndent >= currentIndent {
					break
				}

				logChan <- Token{
					Kind:           Outdent,
					Bytes:          []byte{},
					SourceLocation: *loc,
				}
				indents = indents[:len(indents)-1]
			}
			currentIndent := indents[len(indents)-1]
			if currentIndent != newIndent {
				wrongCount := newIndent - currentIndent

				// Fake up a range of bytes to attach the wrongness to
				// so that we can highlight the error in higher-level
				// diagnostics.
				wrongBytes := make([]byte, wrongCount)
				for i, _ := range wrongBytes {
					wrongBytes[i] = ' '
				}
				// Parser should trap this and produce a diagnostic.
				logChan <- Token{
					Kind:  BadOutdent,
					Bytes: wrongBytes,
					SourceLocation: diagnostics.SourceLocation{
						Filename: loc.Filename,
						Line:     loc.Line,
						Column:   currentIndent,
					},
				}

				// Synthesize an indent level so that we don't
				// keep reporting this mismatch on every subsequent line.
				indents = append(indents, newIndent)
			}
		}

		for {
			tok := <-rawChan
			if tok.Kind == EOF {
				outdentTo(0, &tok.SourceLocation)

				// EOF should always be at the end of the raw stream.
				_, more := <-rawChan
				if more {
					panic(fmt.Errorf("More tokens after EOF"))
				}

				logChan <- tok
				close(logChan)
				return
			}

			switch tok.Kind {
			case OpenBracket:
				bracketCount++
			case CloseBracket:
				bracketCount--
				if bracketCount < 0 {
					tok.Kind = MismatchBracket
					bracketCount = 0
				}
			case Comment:
				// TODO: Special handling for doc comments, which
				// start with #: rather than just #. These need to
				// be included in the logical token stream so that
				// the parser can extract the docs and attach them
				// to whatever they precede in the source file.
				continue
			}

			if bracketCount > 0 {
				if tok.Kind == Space || tok.Kind == NewLine {
					continue
				}
			} else if startOfLine {
				currentIndent := indents[len(indents)-1]
				newIndent := 0
				// TODO: Need to peek ahead and see if there is
				// actually anything other than space on this line,
				// since a blank line or a whitespace-only line should
				// not be considered significant for block structure.
				if tok.Kind == Space {
					newIndent = len(tok.Bytes)
				}
				if newIndent > currentIndent {
					indents = append(indents, newIndent)
					// An indent's "Bytes" are a synthetic bunch of spaces
					// indicating how much new indentation we just added.
					// The parser uses this to emit a warning when indents
					// are not four spaces in size.
					indentBytes := make([]byte, newIndent-currentIndent)
					for i, _ := range indentBytes {
						indentBytes[i] = ' '
					}
					logChan <- Token{
						Kind:           Indent,
						Bytes:          indentBytes,
						SourceLocation: tok.SourceLocation,
					}
				} else if newIndent < currentIndent {
					outdentTo(newIndent, &tok.SourceLocation)
				}
				startOfLine = false

				// We never emit spaces into the logical token stream.
				if tok.Kind == Space {
					continue
				}
			} else if tok.Kind == NewLine {
				// On the next iteration we'll process indentation.
				startOfLine = true
			}

			logChan <- tok
		}
	}()

	return logChan
}
