package aty

// Unknown returns a type variable, which represents a type that isn't yet
// known, such as because it's a template argument.
//
// The expectation is that each type variable will be replaced by a concrete
// type during the type inference phase. Each call to Unknown returns a
// distinct type variable; two type variables are equal only if they trace
// back to the same call to Unknown.
//
// There are no concrete values of a type variable, but an unknown value
// of a type variable can be constructed using UnknownVal.
func Unknown() Type {
	return Type{&typeVar{}}
}

// typeVar is a typeImpl that stands in for a type that isn't yet known.
type typeVar struct {
	isTypeImpl

	// typeVar shouldn't be a zero-length struct since that permits (but
	// doesn't require) the runtime to consider two different instances to be
	// pointer-equal.
	unused int
}

func (t *typeVar) Equals(other Type) bool {
	o, ok := other.impl.(*typeVar)
	if !ok {
		return false
	}

	return t == o
}

func (t *typeVar) ValueEquals(a, b Value) Value {
	// In practice we can never get here because there are no non-unknown
	// values of a type variable. This just satisfies the interface.
	return FalseVal
}
