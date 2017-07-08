package aty

type unknown_ int

const unknown unknown_ = 0

// UnknownVal returns an unknown value of the given type. An unknown value is
// a placeholder for a value that isn't yet known, either because it can't
// be known until runtime or because constant propagation hasn't yet replaced
// it with a concrete value.
func UnknownVal(ty Type) Value {
	return Value{
		ty: ty,
		v:  unknown,
	}
}

// IsKnown returns true if the receiver is a concrete value of its
// type. It returns false if the receiver is an unknown value, created with
// UnknownVal.
func (val Value) IsKnown() bool {
	return val.v == unknown
}

// IsUnknown is the opposite of IsKnown, provided as a convenience.
func (val Value) IsUnknown() bool {
	return !val.IsKnown()
}
