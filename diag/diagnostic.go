package diag

import (
	"bytes"
	"html/template"
	"reflect"
)

type Diagnostic struct {
	Level        Level
	Details      Details
	Range        SourceRange
	ContextRange SourceRange
}

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

// error implementation
func (d *Diagnostic) Error() string {
	return d.MessageHTML()
}
