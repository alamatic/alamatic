package aty

// Value represents an instance of a particular Type.
type Value struct {
	ty Type
	v  interface{}
}

// InvalidVal is the zero value of Value. It is not a valid value, and is used
// only when returned in conjunction with an error to indicate that no
// valid type could be returned.
//
// Calling methods on InvalidVal causes undefined behavior, possibly including
// a panic.
var InvalidVal = Value{}

// Type returns the type of the receiving value.
func (val Value) Type() Type {
	return val.ty
}

// Equals returns TrueVal if the receiver is equal to the given value, or
// FalseVal otherwise.
//
// Equality is defined differently for each type, but two values are never
// equal if they are of different types. (Note: this is not to be confused
// with the behavior of the == operator in the language itself, which is
// able to do certain automatic type conversions to its operands.)
//
// If either value is unknown, the result is UnknownVal(Bool).
func (val Value) Equals(other Value) Value {
	if !val.Type().Equals(other.Type()) {
		return FalseVal
	}

	if val.IsUnknown() || other.IsUnknown() {
		return UnknownVal(Bool)
	}

	return val.Type().impl.ValueEquals(val, other)
}
