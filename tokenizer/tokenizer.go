package tokenizer

import (
	"fmt"

	"github.com/alamatic/alamatic/diag"
)

// Tokenize is the main entry point to the tokenizer.
//
// It takes a byte slice of the source code along with the filename where
// it came from and returns an unbuffered channel that yields the logical
// tokens found in the stream.
func Tokenize(data []byte, filename string) <-chan Token {
	rawChan := Scan(data, filename)
	return RaiseRawTokens(rawChan, 0)
}

// TokenizeExpr is an alternative entry point that produces a
// token stream for a single, isolated expression, rather than for
// an entire module.
//
// The key difference is that expressions can never contain newline,
// indent or outdent tokens. The resulting token stream is not suitable
// for parsing an entire module.
func TokenizeExpr(data []byte, filename string) <-chan Token {
	rawChan := Scan(data, filename)
	return RaiseRawTokens(rawChan, 1)
}

// RaiseRawTokens takes a channel of raw tokens and produces a new channel
// of the corresponding logical tokens.
//
// Most callers should use Tokenize, which wraps this function to produce
// logical tokens directly from source.
func RaiseRawTokens(rawChan <-chan Token, minBracketCount int) <-chan Token {
	logChan := make(chan Token)
	peeker := &TokenPeeker{
		c: rawChan,
	}

	go func() {
		bracketCount := minBracketCount
		indents := make([]int, 0, 20)
		startOfLine := true

		indents = append(indents, 0)

		outdentTo := func(newIndent int, loc *diag.SourceLocation) {
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
					SourceLocation: diag.SourceLocation{
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
			tok := peeker.Read()
			if tok.Kind == EOF {
				outdentTo(0, &tok.SourceLocation)

				// EOF should always be at the end of the raw stream.
				_, more := <-rawChan
				if more {
					panic(fmt.Errorf("More tokens after EOF"))
				}

				logChan <- *tok
				close(logChan)
				return
			}

			switch tok.Kind {
			case OpenBracket:
				bracketCount++
			case CloseBracket:
				bracketCount--
				if bracketCount < minBracketCount {
					tok.Kind = MismatchBracket
					bracketCount = minBracketCount
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
			} else if startOfLine && tok.Kind != NewLine {
				currentIndent := indents[len(indents)-1]
				newIndent := 0
				if tok.Kind == Space {
					newIndent = len(tok.Bytes)
					peeked := peeker.Peek()
					if peeked.Kind == NewLine {
						// Space on a line of its own is not considered
						// to be indentation, so we'll skip it.
						continue
					}
				}
				if newIndent > currentIndent {
					indents = append(indents, newIndent)
					// An indent's "Bytes" are a synthetic bunch of spaces
					// occupying the same source location space that the
					// original space token would've, except that it's still
					// present even if the indent is zero bytes in length.
					indentBytes := make([]byte, newIndent)
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
			} else if tok.Kind == Space {
				// Ignore spaces everywhere except start of line
				continue
			}

			logChan <- *tok
		}
	}()

	return logChan
}
