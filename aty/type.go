package aty

// Type represents a type of value within the intermediate type system.
//
// Instances of this struct are created by various factory functions in this
// package.
type Type struct {
	impl typeImpl
}

// typeImpl is a closed interface (implementable only by types within this
// package) that deals with the various different type behaviors that can
// be wrapped up in a Type instance.
type typeImpl interface {
	isTypeImplMark() isTypeImpl

	Equals(other Type) bool
	ValueEquals(a, b Value) Value
}

// Equals returns true if the given value represents the same type as the
// receiver.
func (t Type) Equals(other Type) bool {
	return t.impl.Equals(other)
}

// Invalid is the zero value of Type. It is not a valid type, and is used
// only when returned in conjunction with an error to indicate that no
// valid type could be returned.
//
// Calling methods on Invalid causes undefined behavior, possibly including
// a panic.
var Invalid = Type{}

type isTypeImpl struct{}

func (i isTypeImpl) isTypeImplMark() isTypeImpl {
	return i
}
