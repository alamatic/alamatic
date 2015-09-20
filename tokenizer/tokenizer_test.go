package tokenizer

import (
	"reflect"
	"testing"
)

// This file re-uses some utilities from scanner_test.go .

func runTokenizeTests(t *testing.T, cases []testCase) {
	for _, c := range cases {
		ch := Tokenize([]byte(c.Input), "")
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

func TestBadBrackets(t *testing.T) {
	runTokenizeTests(t, []testCase{
		testCase{
			")",
			[]Token{
				Token{MismatchBracket, []byte(")"), sloc(1, 1)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
		testCase{
			"())",
			[]Token{
				Token{OpenBracket, []byte("("), sloc(1, 1)},
				Token{CloseBracket, []byte(")"), sloc(1, 2)},
				Token{MismatchBracket, []byte(")"), sloc(1, 3)},
				Token{NewLine, []byte{'\n'}, sloc(2, 0)},
				Token{EOF, []byte{}, sloc(2, 0)},
			},
		},
	})
}

func TestIndentation(t *testing.T) {
	runTokenizeTests(t, []testCase{
		testCase{
			"foo:\n" +
				"    bar",
			[]Token{
				Token{Ident, []byte("foo"), sloc(1, 1)},
				Token{Punct, []byte(":"), sloc(1, 4)},
				Token{NewLine, []byte("\n"), sloc(2, 0)},
				Token{Indent, []byte("    "), sloc(2, 1)},
				Token{Ident, []byte("bar"), sloc(2, 5)},
				Token{NewLine, []byte("\n"), sloc(3, 0)},
				Token{Outdent, []byte(""), sloc(3, 0)},
				Token{EOF, []byte{}, sloc(3, 0)},
			},
		},
		testCase{
			"foo:\n" +
				"    bar\n" +
				"   bar\n" +
				"   bar",
			[]Token{
				Token{Ident, []byte("foo"), sloc(1, 1)},
				Token{Punct, []byte(":"), sloc(1, 4)},
				Token{NewLine, []byte("\n"), sloc(2, 0)},
				Token{Indent, []byte("    "), sloc(2, 1)},
				Token{Ident, []byte("bar"), sloc(2, 5)},
				Token{NewLine, []byte("\n"), sloc(3, 0)},
				Token{Outdent, []byte(""), sloc(3, 1)},
				Token{BadOutdent, []byte("   "), sloc(3, 0)},
				Token{Ident, []byte("bar"), sloc(3, 4)},
				Token{NewLine, []byte("\n"), sloc(4, 0)},
				Token{Ident, []byte("bar"), sloc(4, 4)},
				Token{NewLine, []byte("\n"), sloc(5, 0)},
				Token{Outdent, []byte(""), sloc(5, 0)},
				Token{EOF, []byte{}, sloc(5, 0)},
			},
		},
		testCase{
			"(foo:\n" +
				"    bar)",
			[]Token{
				Token{OpenBracket, []byte("("), sloc(1, 1)},
				Token{Ident, []byte("foo"), sloc(1, 2)},
				Token{Punct, []byte(":"), sloc(1, 5)},
				Token{Ident, []byte("bar"), sloc(2, 5)},
				Token{CloseBracket, []byte(")"), sloc(2, 8)},
				Token{NewLine, []byte("\n"), sloc(3, 0)},
				Token{EOF, []byte{}, sloc(3, 0)},
			},
		},
		testCase{
			"foo\n    bar\n    baz\n        boo\n    bur",
			[]Token{
				Token{Ident, []byte("foo"), sloc(1, 1)},
				Token{NewLine, []byte("\n"), sloc(2, 0)},
				Token{Indent, []byte("    "), sloc(2, 1)},
				Token{Ident, []byte("bar"), sloc(2, 5)},
				Token{NewLine, []byte("\n"), sloc(3, 0)},
				Token{Ident, []byte("baz"), sloc(3, 5)},
				Token{NewLine, []byte("\n"), sloc(4, 0)},
				Token{Indent, []byte("        "), sloc(4, 1)},
				Token{Ident, []byte("boo"), sloc(4, 9)},
				Token{NewLine, []byte("\n"), sloc(5, 0)},
				Token{Outdent, []byte(""), sloc(5, 1)},
				Token{Ident, []byte("bur"), sloc(5, 5)},
				Token{NewLine, []byte("\n"), sloc(6, 0)},
				Token{Outdent, []byte(""), sloc(6, 0)},
				Token{EOF, []byte{}, sloc(6, 0)},
			},
		},
		testCase{
			"foo\n    bar\n\n    boo",
			[]Token{
				Token{Ident, []byte("foo"), sloc(1, 1)},
				Token{NewLine, []byte("\n"), sloc(2, 0)},
				Token{Indent, []byte("    "), sloc(2, 1)},
				Token{Ident, []byte("bar"), sloc(2, 5)},
				Token{NewLine, []byte("\n"), sloc(3, 0)},
				Token{NewLine, []byte("\n"), sloc(4, 0)},
				Token{Ident, []byte("boo"), sloc(4, 5)},
				Token{NewLine, []byte("\n"), sloc(5, 0)},
				Token{Outdent, []byte(""), sloc(5, 0)},
				Token{EOF, []byte{}, sloc(5, 0)},
			},
		},
		testCase{
			"foo\n    bar\n  \n    boo",
			[]Token{
				Token{Ident, []byte("foo"), sloc(1, 1)},
				Token{NewLine, []byte("\n"), sloc(2, 0)},
				Token{Indent, []byte("    "), sloc(2, 1)},
				Token{Ident, []byte("bar"), sloc(2, 5)},
				Token{NewLine, []byte("\n"), sloc(3, 0)},
				Token{NewLine, []byte("\n"), sloc(4, 0)},
				Token{Ident, []byte("boo"), sloc(4, 5)},
				Token{NewLine, []byte("\n"), sloc(5, 0)},
				Token{Outdent, []byte(""), sloc(5, 0)},
				Token{EOF, []byte{}, sloc(5, 0)},
			},
		},
	})
}
