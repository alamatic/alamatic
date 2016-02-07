package diag

import (
	"testing"
)

type TestDetailsSimple struct {
	Message `<code>{{.VarName}}</code> is of type <code>{{.TypeName}}</code>!`

	VarName  string
	TypeName string
}

func TestDiagnosticMessageHTML(t *testing.T) {
	details := &TestDetailsSimple{
		VarName:  "a",
		TypeName: "Bool",
	}
	diag := &Diagnostic{
		Level:   Error,
		Details: details,
	}
	{
		got := diag.MessageHTML()
		expected := "<code>a</code> is of type <code>Bool</code>!"
		if got != expected {
			t.Errorf("Got %#v; want %#v", got, expected)
		}
	}
	details.TypeName = "<foo>"
	{
		got := diag.MessageHTML()
		expected := "<code>a</code> is of type <code>&lt;foo&gt;</code>!"
		if got != expected {
			t.Errorf("Got %#v; want %#v", got, expected)
		}
	}
}
