package diag

import (
	"reflect"
)

// Details is an empty placeholder interface that exists only for documentation.
//
// The diagnostic details mechanism allows code that creates a diagnostic to
// provide the diagnostic-type-specific data and configuration. This is done
// statically, by creating a struct containing whatever data is needed to
// produce a diagnostic message, and then embedding the empty struct
// Message with a field tag containing the template for rendering the message.
type Details interface {
	DummyMessageDetectingMethod_()
}

// Message is an empty struct that should be embedded in a diagnostic details
// struct, and tagged with a template for rendering the diagnostic message to
// a subset of HTML.
//
// The HTML subset currently consists only of regular text and non-nested
// 'code' elements that represent Alamatic source code fragments.
//
// The (empty) instance of this type is not actually used. Instead, the
// Message method of Diagnostic will use reflection to obtain the Message tag,
// and render the obtained template using the containing diagnostic details
// struct instance as the context.
type Message struct {
}

var messageType = reflect.TypeOf(Message{})

func (*Message) DummyMessageDetectingMethod_() {
	// This does nothing and is here only so that structs embedding Message
	// will implement the Details interface.
}
