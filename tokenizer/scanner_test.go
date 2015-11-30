package tokenizer

import (
	"reflect"
	"testing"

	"github.com/alamatic/alamatic/diag"
)

type testCase struct {
	Input    string
	Expected []Token
}

func runScanTests(t *testing.T, cases []testCase) {
	for _, c := range cases {
		ch := Scan([]byte(c.Input), "")
		got := []Token{}
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

func sloc(line int, column int) diag.SourceLocation {
	return diag.SourceLocation{"", line, column}
}

func TestNumLitLiterals(t *testing.T) {
	runScanTests(t, []testCase{
		testCase{
			"150",
			[]Token{
				Token{DecNumLit, []byte("150"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"0x123abcz123",
			[]Token{
				Token{HexNumLit, []byte("0x123abcz123"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"0b12345",
			[]Token{
				Token{BinNumLit, []byte("0b12345"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"0o12389",
			[]Token{
				Token{OctNumLit, []byte("0o12389"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
	})
}

func TestStringLiterals(t *testing.T) {
	runScanTests(t, []testCase{
		testCase{
			`"hello"`,
			[]Token{
				Token{StringLit, []byte(`"hello"`), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			`"woo \" woo"`,
			[]Token{
				Token{StringLit, []byte(`"woo \" woo"`), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			`"woo\nwoo"`,
			[]Token{
				Token{StringLit, []byte("\"woo\\nwoo\""), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},

		// Unending strings
		testCase{
			`"woo\"`,
			[]Token{
				Token{StringLit, []byte("\"woo\\\""), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			`"woo\"woo`,
			[]Token{
				Token{StringLit, []byte("\"woo\\\"woo"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			`"woo`,
			[]Token{
				Token{StringLit, []byte("\"woo"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
	})
}

func TestPunctuation(t *testing.T) {
	runScanTests(t, []testCase{
		testCase{
			"|",
			[]Token{
				Token{Punct, []byte{'|'}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"|=",
			[]Token{
				Token{Punct, []byte{'|', '='}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"&",
			[]Token{
				Token{Punct, []byte{'&'}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"&=",
			[]Token{
				Token{Punct, []byte{'&', '='}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"^",
			[]Token{
				Token{Punct, []byte{'^'}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"^=",
			[]Token{
				Token{Punct, []byte{'^', '='}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"=",
			[]Token{
				Token{Punct, []byte{'='}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"=",
			[]Token{
				Token{Punct, []byte{'='}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"+",
			[]Token{
				Token{Punct, []byte{'+'}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			// Invalid combinations become only one token.
			// (The parser is responsible for detecting invalid operators)
			"+-!",
			[]Token{
				Token{Punct, []byte{'+', '-', '!'}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
	})
}

func TestBrackets(t *testing.T) {
	runScanTests(t, []testCase{
		testCase{
			"(",
			[]Token{
				Token{OpenBracket, []byte{'('}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			// Consecutive brackets don't combine together like the
			// operator punctuation characters.
			"((",
			[]Token{
				Token{OpenBracket, []byte{'('}, sloc(1, 1)},
				Token{OpenBracket, []byte{'('}, sloc(1, 2)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			")",
			[]Token{
				Token{CloseBracket, []byte{')'}, sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"))",
			[]Token{
				Token{CloseBracket, []byte{')'}, sloc(1, 1)},
				Token{CloseBracket, []byte{')'}, sloc(1, 2)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"([{",
			[]Token{
				Token{OpenBracket, []byte{'('}, sloc(1, 1)},
				Token{OpenBracket, []byte{'['}, sloc(1, 2)},
				Token{OpenBracket, []byte{'{'}, sloc(1, 3)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"([{)]}",
			[]Token{
				Token{OpenBracket, []byte{'('}, sloc(1, 1)},
				Token{OpenBracket, []byte{'['}, sloc(1, 2)},
				Token{OpenBracket, []byte{'{'}, sloc(1, 3)},
				Token{CloseBracket, []byte{')'}, sloc(1, 4)},
				Token{CloseBracket, []byte{']'}, sloc(1, 5)},
				Token{CloseBracket, []byte{'}'}, sloc(1, 6)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
	})
}

func TestIdentifiers(t *testing.T) {
	runScanTests(t, []testCase{
		testCase{
			"hello",
			[]Token{
				Token{Ident, []byte("hello"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"hello_world",
			[]Token{
				Token{Ident, []byte("hello_world"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"_world",
			[]Token{
				Token{Ident, []byte("_world"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"world123",
			[]Token{
				Token{Ident, []byte("world123"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
	})
}

func TestSpaces(t *testing.T) {
	runScanTests(t, []testCase{
		testCase{
			"     ",
			[]Token{
				Token{Space, []byte("     "), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			" ",
			[]Token{
				Token{Space, []byte(" "), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"\n",
			[]Token{
				Token{NewLine, []byte("\n"), sloc(2, 0)},
				Token{NewLine, []byte{'\n'}, sloc(3, 0)},
				Token{EOF, []byte{}, sloc(3, 0)},
			},
		},
		testCase{
			"\n\n\n",
			[]Token{
				// These read as column 0 because the newline character
				// itself is "between" the lines for the purpose of our
				// counting.
				Token{NewLine, []byte("\n"), sloc(2, 0)},
				Token{NewLine, []byte("\n"), sloc(3, 0)},
				Token{NewLine, []byte("\n"), sloc(4, 0)},
				Token{NewLine, []byte{'\n'}, sloc(5, 0)},
				Token{EOF, []byte{}, sloc(5, 0)},
			},
		},
		testCase{
			"\r\n\r\n\r\n",
			[]Token{
				// These read as column -1 because we place the \n at
				// column 0, and the \r precedes it. This is just
				// an implementation detail really, since nobody
				// actually cares where the newlines are.
				Token{NewLine, []byte("\r\n"), sloc(2, -1)},
				Token{NewLine, []byte("\r\n"), sloc(3, -1)},
				Token{NewLine, []byte("\r\n"), sloc(4, -1)},
				Token{NewLine, []byte{'\n'}, sloc(5, 0)},
				Token{EOF, []byte{}, sloc(5, 0)},
			},
		},
		testCase{
			"# hello",
			[]Token{
				Token{Comment, []byte("# hello"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"## hello",
			[]Token{
				Token{Comment, []byte("## hello"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"#",
			[]Token{
				Token{Comment, []byte("#"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"# hello\n# hello",
			[]Token{
				Token{Comment, []byte("# hello"), sloc(1, 1)},
				Token{NewLine, []byte("\n"), sloc(2, 0)},
				Token{Comment, []byte("# hello"), sloc(2, 1)},
				Token{NewLine, []byte{'\n'}, sloc(3, 0)},
				Token{EOF, []byte{}, sloc(3, 0)},
			},
		},
		testCase{
			"    # hello\n    # hello",
			[]Token{
				Token{Space, []byte("    "), sloc(1, 1)},
				Token{Comment, []byte("# hello"), sloc(1, 5)},
				Token{NewLine, []byte("\n"), sloc(2, 0)},
				Token{Space, []byte("    "), sloc(2, 1)},
				Token{Comment, []byte("# hello"), sloc(2, 5)},
				Token{NewLine, []byte{'\n'}, sloc(3, 0)},
				Token{EOF, []byte{}, sloc(3, 0)},
			},
		},
	})
}

func TestCombinations(t *testing.T) {
	runScanTests(t, []testCase{
		testCase{
			"12+2",
			[]Token{
				Token{DecNumLit, []byte("12"), sloc(1, 1)},
				Token{Punct, []byte("+"), sloc(1, 3)},
				Token{DecNumLit, []byte("2"), sloc(1, 4)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"12 + 2",
			[]Token{
				Token{DecNumLit, []byte("12"), sloc(1, 1)},
				Token{Space, []byte(" "), sloc(1, 3)},
				Token{Punct, []byte("+"), sloc(1, 4)},
				Token{Space, []byte(" "), sloc(1, 5)},
				Token{DecNumLit, []byte("2"), sloc(1, 6)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"foo()",
			[]Token{
				Token{Ident, []byte("foo"), sloc(1, 1)},
				Token{OpenBracket, []byte("("), sloc(1, 4)},
				Token{CloseBracket, []byte(")"), sloc(1, 5)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"1+=(2+foo)",
			[]Token{
				Token{DecNumLit, []byte("1"), sloc(1, 1)},
				Token{Punct, []byte("+="), sloc(1, 2)},
				Token{OpenBracket, []byte("("), sloc(1, 4)},
				Token{DecNumLit, []byte("2"), sloc(1, 5)},
				Token{Punct, []byte("+"), sloc(1, 6)},
				Token{Ident, []byte("foo"), sloc(1, 7)},
				Token{CloseBracket, []byte(")"), sloc(1, 10)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			`foo.baz[] .. ["thing"]`,
			[]Token{
				Token{Ident, []byte("foo"), sloc(1, 1)},
				Token{Punct, []byte("."), sloc(1, 4)},
				Token{Ident, []byte("baz"), sloc(1, 5)},
				Token{OpenBracket, []byte("["), sloc(1, 8)},
				Token{CloseBracket, []byte("]"), sloc(1, 9)},
				Token{Space, []byte(" "), sloc(1, 10)},
				Token{Punct, []byte(".."), sloc(1, 11)},
				Token{Space, []byte(" "), sloc(1, 13)},
				Token{OpenBracket, []byte("["), sloc(1, 14)},
				Token{StringLit, []byte(`"thing"`), sloc(1, 15)},
				Token{CloseBracket, []byte("]"), sloc(1, 22)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
	})
}
