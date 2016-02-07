package diag

import (
	"bytes"
	"html/template"
	"reflect"
)

// Diagnostic represents a single diagnostic message referring to a particular
// source code range.
//
// The diagnostics system is designed such that each distinct diagnostic type
// is represented as a different Go type, with that type containing the
// specific parameters required for the message. These diagnostic-type-specific
// objects appear in the Details field.
//
// Templates for diagnostic messages are defined within the type system as
// struct tags. See the Details interface for more information.
type Diagnostic struct {
	Level              Level
	Details            Details
	SourceRange        *SourceRange
	ContextSourceRange *SourceRange
}

// MessageHTML returns a string containing an HTML fragment representing the
// diagnostic's message.
//
// At present only the <code> element type has a defined meaning in the subset
// of HTML used in diagnostic messages: it delimits fragments of Alamatic
// source code.
//
// New element types may be allowed in future. Users of the provided HTML that
// interpret the HTML within should skip the delimeters of any element they do
// not understand, and process the content within as if the element delimeters
// were not present.
func (d *Diagnostic) MessageHTML() string {
	// This is a bit tricky.
	// To help the rest of the program easily define diagnostic messages,
	// the Details member is any arbitrary struct that embeds the empty
	// Message struct. We use the tag on that embedded struct as a template
	// and render it with the details instance as its context.
	dType := reflect.TypeOf(d.Details).Elem()

	field, ok := dType.FieldByName("Message")
	if !ok {
		return dType.String()
	}

	if field.Type != messageType {
		// Apparently this object has a "Message" member that
		// *isn't* a Message tag tag.
		return dType.String()
	}

	tmpl, err := template.New(dType.Name()).Parse(string(field.Tag))
	if err != nil {
		return dType.String()
	}

	buf := &bytes.Buffer{}
	err = tmpl.Execute(buf, d.Details)
	if err != nil {
		return dType.String()
	}

	return buf.String()
}

// Error is present so that Diagnostic implements the error interface.
//
// In regular codepaths diagnostics are not used as Go errors, since the
// Alamatic processing path uses in-band diagnostic signalling to permit
// error recovery and prioritization of multiple reported errors. This
// method is therefore provided only for convenience in test/debug code.
func (d *Diagnostic) Error() string {
	return d.MessageHTML()
}
