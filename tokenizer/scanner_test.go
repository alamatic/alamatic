package tokenizer

import (
	"reflect"
	"testing"
)

type testCase struct {
	Input    string
	Expected []RawToken
}

func runTests(t *testing.T, cases []testCase) {
	for _, c := range cases {
		ch := Scan([]byte(c.Input))
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

func TestNumLitLiterals(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"150",
			[]RawToken{
				RawToken{DecNumLit, []byte("150")},
			},
		},
		testCase{
			"0x123abcz123",
			[]RawToken{
				RawToken{HexNumLit, []byte("0x123abcz123")},
			},
		},
		testCase{
			"0b12345",
			[]RawToken{
				RawToken{BinNumLit, []byte("0b12345")},
			},
		},
		testCase{
			"0o12389",
			[]RawToken{
				RawToken{OctNumLit, []byte("0o12389")},
			},
		},
	})
}

func TestStringLiterals(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			`"hello"`,
			[]RawToken{
				RawToken{StringLit, []byte(`"hello"`)},
			},
		},
		testCase{
			`"woo \" woo"`,
			[]RawToken{
				RawToken{StringLit, []byte(`"woo \" woo"`)},
			},
		},
		testCase{
			`"woo\nwoo"`,
			[]RawToken{
				RawToken{StringLit, []byte("\"woo\\nwoo\"")},
			},
		},

		// Unending strings
		testCase{
			`"woo\"`,
			[]RawToken{
				RawToken{StringLit, []byte("\"woo\\\"")},
			},
		},
		testCase{
			`"woo\"woo`,
			[]RawToken{
				RawToken{StringLit, []byte("\"woo\\\"woo")},
			},
		},
		testCase{
			`"woo`,
			[]RawToken{
				RawToken{StringLit, []byte("\"woo")},
			},
		},
	})
}

func TestPunctuation(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"|",
			[]RawToken{
				RawToken{Punct, []byte{'|'}},
			},
		},
		testCase{
			"|=",
			[]RawToken{
				RawToken{Punct, []byte{'|', '='}},
			},
		},
		testCase{
			"&",
			[]RawToken{
				RawToken{Punct, []byte{'&'}},
			},
		},
		testCase{
			"&=",
			[]RawToken{
				RawToken{Punct, []byte{'&', '='}},
			},
		},
		testCase{
			"^",
			[]RawToken{
				RawToken{Punct, []byte{'^'}},
			},
		},
		testCase{
			"^=",
			[]RawToken{
				RawToken{Punct, []byte{'^', '='}},
			},
		},
		testCase{
			"=",
			[]RawToken{
				RawToken{Punct, []byte{'='}},
			},
		},
		testCase{
			"=",
			[]RawToken{
				RawToken{Punct, []byte{'='}},
			},
		},
		testCase{
			"+",
			[]RawToken{
				RawToken{Punct, []byte{'+'}},
			},
		},
		testCase{
			// Invalid combinations become only one token.
			// (The parser is responsible for detecting invalid operators)
			"+-!",
			[]RawToken{
				RawToken{Punct, []byte{'+', '-', '!'}},
			},
		},
	})
}

func TestBrackets(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"(",
			[]RawToken{
				RawToken{OpenBracket, []byte{'('}},
			},
		},
		testCase{
			// Consecutive brackets don't combine together like the
			// operator punctuation characters.
			"((",
			[]RawToken{
				RawToken{OpenBracket, []byte{'('}},
				RawToken{OpenBracket, []byte{'('}},
			},
		},
		testCase{
			")",
			[]RawToken{
				RawToken{CloseBracket, []byte{')'}},
			},
		},
		testCase{
			"))",
			[]RawToken{
				RawToken{CloseBracket, []byte{')'}},
				RawToken{CloseBracket, []byte{')'}},
			},
		},
		testCase{
			"([{",
			[]RawToken{
				RawToken{OpenBracket, []byte{'('}},
				RawToken{OpenBracket, []byte{'['}},
				RawToken{OpenBracket, []byte{'{'}},
			},
		},
		testCase{
			"([{)]}",
			[]RawToken{
				RawToken{OpenBracket, []byte{'('}},
				RawToken{OpenBracket, []byte{'['}},
				RawToken{OpenBracket, []byte{'{'}},
				RawToken{CloseBracket, []byte{')'}},
				RawToken{CloseBracket, []byte{']'}},
				RawToken{CloseBracket, []byte{'}'}},
			},
		},
	})
}

func TestIdentifiers(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"hello",
			[]RawToken{
				RawToken{Ident, []byte("hello")},
			},
		},
		testCase{
			"hello_world",
			[]RawToken{
				RawToken{Ident, []byte("hello_world")},
			},
		},
		testCase{
			"_world",
			[]RawToken{
				RawToken{Ident, []byte("_world")},
			},
		},
		testCase{
			"world123",
			[]RawToken{
				RawToken{Ident, []byte("world123")},
			},
		},
	})
}

func TestSpaces(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"     ",
			[]RawToken{
				RawToken{Space, []byte("     ")},
			},
		},
		testCase{
			" ",
			[]RawToken{
				RawToken{Space, []byte(" ")},
			},
		},
		testCase{
			"\n",
			[]RawToken{
				RawToken{NewLine, []byte("\n")},
			},
		},
		testCase{
			"\n\n\n",
			[]RawToken{
				RawToken{NewLine, []byte("\n")},
				RawToken{NewLine, []byte("\n")},
				RawToken{NewLine, []byte("\n")},
			},
		},
		testCase{
			"\r\n\r\n\r\n",
			[]RawToken{
				RawToken{NewLine, []byte("\r\n")},
				RawToken{NewLine, []byte("\r\n")},
				RawToken{NewLine, []byte("\r\n")},
			},
		},
		testCase{
			"# hello",
			[]RawToken{
				RawToken{Comment, []byte("# hello")},
			},
		},
		testCase{
			"## hello",
			[]RawToken{
				RawToken{Comment, []byte("## hello")},
			},
		},
		testCase{
			"#",
			[]RawToken{
				RawToken{Comment, []byte("#")},
			},
		},
		testCase{
			"# hello\n# hello",
			[]RawToken{
				RawToken{Comment, []byte("# hello")},
				RawToken{NewLine, []byte("\n")},
				RawToken{Comment, []byte("# hello")},
			},
		},
		testCase{
			"    # hello\n    # hello",
			[]RawToken{
				RawToken{Space, []byte("    ")},
				RawToken{Comment, []byte("# hello")},
				RawToken{NewLine, []byte("\n")},
				RawToken{Space, []byte("    ")},
				RawToken{Comment, []byte("# hello")},
			},
		},
	})
}

func TestCombinations(t *testing.T) {
	runTests(t, []testCase{
		testCase{
			"12+2",
			[]RawToken{
				RawToken{DecNumLit, []byte("12")},
				RawToken{Punct, []byte("+")},
				RawToken{DecNumLit, []byte("2")},
			},
		},
		testCase{
			"12 + 2",
			[]RawToken{
				RawToken{DecNumLit, []byte("12")},
				RawToken{Space, []byte(" ")},
				RawToken{Punct, []byte("+")},
				RawToken{Space, []byte(" ")},
				RawToken{DecNumLit, []byte("2")},
			},
		},
		testCase{
			"foo()",
			[]RawToken{
				RawToken{Ident, []byte("foo")},
				RawToken{OpenBracket, []byte("(")},
				RawToken{CloseBracket, []byte(")")},
			},
		},
		testCase{
			"1+=(2+foo)",
			[]RawToken{
				RawToken{DecNumLit, []byte("1")},
				RawToken{Punct, []byte("+=")},
				RawToken{OpenBracket, []byte("(")},
				RawToken{DecNumLit, []byte("2")},
				RawToken{Punct, []byte("+")},
				RawToken{Ident, []byte("foo")},
				RawToken{CloseBracket, []byte(")")},
			},
		},
		testCase{
			`foo.baz[] .. ["thing"]`,
			[]RawToken{
				RawToken{Ident, []byte("foo")},
				RawToken{Punct, []byte(".")},
				RawToken{Ident, []byte("baz")},
				RawToken{OpenBracket, []byte("[")},
				RawToken{CloseBracket, []byte("]")},
				RawToken{Space, []byte(" ")},
				RawToken{Punct, []byte("..")},
				RawToken{Space, []byte(" ")},
				RawToken{OpenBracket, []byte("[")},
				RawToken{StringLit, []byte(`"thing"`)},
				RawToken{CloseBracket, []byte("]")},
			},
		},
	})
}
