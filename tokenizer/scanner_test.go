package tokenizer

import (
	"reflect"
	"testing"

	"github.com/alamatic/alamatic/diagnostics"
)

type testCase struct {
	Input    string
	Expected []RawToken
}

func runTests(t *testing.T, cases []testCase) {
	for _, c := range cases {
		ch := Scan([]byte(c.Input), "")
		got := []RawToken{}
		for tok := range ch {
			got = append(got, tok)
		}

		if !reflect.DeepEqual(got, c.Expected) {
			t.Errorf("----------")
			t.Errorf("Test Input: %s", c.Input)
			t.Errorf("Got:")
			for _, tok := range got {
				t.Errorf("    %s", tok)
			}
			t.Errorf("Want:")
			for _, tok := range c.Expected {
				t.Errorf("    %s", tok)
			}
		}
	}
}

func sloc(line int, column int) diagnostics.SourceLocation {
	return diagnostics.SourceLocation{"", line, column}
}

func TestNumLitLiterals(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"150",
			[]RawToken{
				RawToken{DecNumLit, []byte("150"), sloc(1, 1)},
			},
		},
		testCase{
			"0x123abcz123",
			[]RawToken{
				RawToken{HexNumLit, []byte("0x123abcz123"), sloc(1, 1)},
			},
		},
		testCase{
			"0b12345",
			[]RawToken{
				RawToken{BinNumLit, []byte("0b12345"), sloc(1, 1)},
			},
		},
		testCase{
			"0o12389",
			[]RawToken{
				RawToken{OctNumLit, []byte("0o12389"), sloc(1, 1)},
			},
		},
	})
}

func TestStringLiterals(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			`"hello"`,
			[]RawToken{
				RawToken{StringLit, []byte(`"hello"`), sloc(1, 1)},
			},
		},
		testCase{
			`"woo \" woo"`,
			[]RawToken{
				RawToken{StringLit, []byte(`"woo \" woo"`), sloc(1, 1)},
			},
		},
		testCase{
			`"woo\nwoo"`,
			[]RawToken{
				RawToken{StringLit, []byte("\"woo\\nwoo\""), sloc(1, 1)},
			},
		},

		// Unending strings
		testCase{
			`"woo\"`,
			[]RawToken{
				RawToken{StringLit, []byte("\"woo\\\""), sloc(1, 1)},
			},
		},
		testCase{
			`"woo\"woo`,
			[]RawToken{
				RawToken{StringLit, []byte("\"woo\\\"woo"), sloc(1, 1)},
			},
		},
		testCase{
			`"woo`,
			[]RawToken{
				RawToken{StringLit, []byte("\"woo"), sloc(1, 1)},
			},
		},
	})
}

func TestPunctuation(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"|",
			[]RawToken{
				RawToken{Punct, []byte{'|'}, sloc(1, 1)},
			},
		},
		testCase{
			"|=",
			[]RawToken{
				RawToken{Punct, []byte{'|', '='}, sloc(1, 1)},
			},
		},
		testCase{
			"&",
			[]RawToken{
				RawToken{Punct, []byte{'&'}, sloc(1, 1)},
			},
		},
		testCase{
			"&=",
			[]RawToken{
				RawToken{Punct, []byte{'&', '='}, sloc(1, 1)},
			},
		},
		testCase{
			"^",
			[]RawToken{
				RawToken{Punct, []byte{'^'}, sloc(1, 1)},
			},
		},
		testCase{
			"^=",
			[]RawToken{
				RawToken{Punct, []byte{'^', '='}, sloc(1, 1)},
			},
		},
		testCase{
			"=",
			[]RawToken{
				RawToken{Punct, []byte{'='}, sloc(1, 1)},
			},
		},
		testCase{
			"=",
			[]RawToken{
				RawToken{Punct, []byte{'='}, sloc(1, 1)},
			},
		},
		testCase{
			"+",
			[]RawToken{
				RawToken{Punct, []byte{'+'}, sloc(1, 1)},
			},
		},
		testCase{
			// Invalid combinations become only one token.
			// (The parser is responsible for detecting invalid operators)
			"+-!",
			[]RawToken{
				RawToken{Punct, []byte{'+', '-', '!'}, sloc(1, 1)},
			},
		},
	})
}

func TestBrackets(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"(",
			[]RawToken{
				RawToken{OpenBracket, []byte{'('}, sloc(1, 1)},
			},
		},
		testCase{
			// Consecutive brackets don't combine together like the
			// operator punctuation characters.
			"((",
			[]RawToken{
				RawToken{OpenBracket, []byte{'('}, sloc(1, 1)},
				RawToken{OpenBracket, []byte{'('}, sloc(1, 2)},
			},
		},
		testCase{
			")",
			[]RawToken{
				RawToken{CloseBracket, []byte{')'}, sloc(1, 1)},
			},
		},
		testCase{
			"))",
			[]RawToken{
				RawToken{CloseBracket, []byte{')'}, sloc(1, 1)},
				RawToken{CloseBracket, []byte{')'}, sloc(1, 2)},
			},
		},
		testCase{
			"([{",
			[]RawToken{
				RawToken{OpenBracket, []byte{'('}, sloc(1, 1)},
				RawToken{OpenBracket, []byte{'['}, sloc(1, 2)},
				RawToken{OpenBracket, []byte{'{'}, sloc(1, 3)},
			},
		},
		testCase{
			"([{)]}",
			[]RawToken{
				RawToken{OpenBracket, []byte{'('}, sloc(1, 1)},
				RawToken{OpenBracket, []byte{'['}, sloc(1, 2)},
				RawToken{OpenBracket, []byte{'{'}, sloc(1, 3)},
				RawToken{CloseBracket, []byte{')'}, sloc(1, 4)},
				RawToken{CloseBracket, []byte{']'}, sloc(1, 5)},
				RawToken{CloseBracket, []byte{'}'}, sloc(1, 6)},
			},
		},
	})
}

func TestIdentifiers(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"hello",
			[]RawToken{
				RawToken{Ident, []byte("hello"), sloc(1, 1)},
			},
		},
		testCase{
			"hello_world",
			[]RawToken{
				RawToken{Ident, []byte("hello_world"), sloc(1, 1)},
			},
		},
		testCase{
			"_world",
			[]RawToken{
				RawToken{Ident, []byte("_world"), sloc(1, 1)},
			},
		},
		testCase{
			"world123",
			[]RawToken{
				RawToken{Ident, []byte("world123"), sloc(1, 1)},
			},
		},
	})
}

func TestSpaces(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"     ",
			[]RawToken{
				RawToken{Space, []byte("     "), sloc(1, 1)},
			},
		},
		testCase{
			" ",
			[]RawToken{
				RawToken{Space, []byte(" "), sloc(1, 1)},
			},
		},
		testCase{
			"\n",
			[]RawToken{
				RawToken{NewLine, []byte("\n"), sloc(2, 0)},
			},
		},
		testCase{
			"\n\n\n",
			[]RawToken{
				// These read as column 0 because the newline character
				// itself is "between" the lines for the purpose of our
				// counting.
				RawToken{NewLine, []byte("\n"), sloc(2, 0)},
				RawToken{NewLine, []byte("\n"), sloc(3, 0)},
				RawToken{NewLine, []byte("\n"), sloc(4, 0)},
			},
		},
		testCase{
			"\r\n\r\n\r\n",
			[]RawToken{
				// These read as column -1 because we place the \n at
				// column 0, and the \r precedes it. This is just
				// an implementation detail really, since nobody
				// actually cares where the newlines are.
				RawToken{NewLine, []byte("\r\n"), sloc(2, -1)},
				RawToken{NewLine, []byte("\r\n"), sloc(3, -1)},
				RawToken{NewLine, []byte("\r\n"), sloc(4, -1)},
			},
		},
		testCase{
			"# hello",
			[]RawToken{
				RawToken{Comment, []byte("# hello"), sloc(1, 1)},
			},
		},
		testCase{
			"## hello",
			[]RawToken{
				RawToken{Comment, []byte("## hello"), sloc(1, 1)},
			},
		},
		testCase{
			"#",
			[]RawToken{
				RawToken{Comment, []byte("#"), sloc(1, 1)},
			},
		},
		testCase{
			"# hello\n# hello",
			[]RawToken{
				RawToken{Comment, []byte("# hello"), sloc(1, 1)},
				RawToken{NewLine, []byte("\n"), sloc(2, 0)},
				RawToken{Comment, []byte("# hello"), sloc(2, 1)},
			},
		},
		testCase{
			"    # hello\n    # hello",
			[]RawToken{
				RawToken{Space, []byte("    "), sloc(1, 1)},
				RawToken{Comment, []byte("# hello"), sloc(1, 5)},
				RawToken{NewLine, []byte("\n"), sloc(2, 0)},
				RawToken{Space, []byte("    "), sloc(2, 1)},
				RawToken{Comment, []byte("# hello"), sloc(2, 5)},
			},
		},
	})
}

func TestCombinations(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"12+2",
			[]RawToken{
				RawToken{DecNumLit, []byte("12"), sloc(1, 1)},
				RawToken{Punct, []byte("+"), sloc(1, 3)},
				RawToken{DecNumLit, []byte("2"), sloc(1, 4)},
			},
		},
		testCase{
			"12 + 2",
			[]RawToken{
				RawToken{DecNumLit, []byte("12"), sloc(1, 1)},
				RawToken{Space, []byte(" "), sloc(1, 3)},
				RawToken{Punct, []byte("+"), sloc(1, 4)},
				RawToken{Space, []byte(" "), sloc(1, 5)},
				RawToken{DecNumLit, []byte("2"), sloc(1, 6)},
			},
		},
		testCase{
			"foo()",
			[]RawToken{
				RawToken{Ident, []byte("foo"), sloc(1, 1)},
				RawToken{OpenBracket, []byte("("), sloc(1, 4)},
				RawToken{CloseBracket, []byte(")"), sloc(1, 5)},
			},
		},
		testCase{
			"1+=(2+foo)",
			[]RawToken{
				RawToken{DecNumLit, []byte("1"), sloc(1, 1)},
				RawToken{Punct, []byte("+="), sloc(1, 2)},
				RawToken{OpenBracket, []byte("("), sloc(1, 4)},
				RawToken{DecNumLit, []byte("2"), sloc(1, 5)},
				RawToken{Punct, []byte("+"), sloc(1, 6)},
				RawToken{Ident, []byte("foo"), sloc(1, 7)},
				RawToken{CloseBracket, []byte(")"), sloc(1, 10)},
			},
		},
		testCase{
			`foo.baz[] .. ["thing"]`,
			[]RawToken{
				RawToken{Ident, []byte("foo"), sloc(1, 1)},
				RawToken{Punct, []byte("."), sloc(1, 4)},
				RawToken{Ident, []byte("baz"), sloc(1, 5)},
				RawToken{OpenBracket, []byte("["), sloc(1, 8)},
				RawToken{CloseBracket, []byte("]"), sloc(1, 9)},
				RawToken{Space, []byte(" "), sloc(1, 10)},
				RawToken{Punct, []byte(".."), sloc(1, 11)},
				RawToken{Space, []byte(" "), sloc(1, 13)},
				RawToken{OpenBracket, []byte("["), sloc(1, 14)},
				RawToken{StringLit, []byte(`"thing"`), sloc(1, 15)},
				RawToken{CloseBracket, []byte("]"), sloc(1, 22)},
			},
		},
	})
}
