package aty

// Maybe constructs and returns a "maybe type", which represents a union of
// the given type and the special Null type. Maybe values must be "unwrapped"
// before use, by proving that they are not null.
func Maybe(elem Type) Type {
	return Type{maybe{elem: elem}}
}

type maybe struct {
	isTypeImpl

	elem Type
}

func (t maybe) Equals(other Type) bool {
	switch ot := other.impl.(type) {
	case maybe:
		return ot.elem.Equals(t.elem)
	default:
		return false
	}
}

func (t maybe) ValueEquals(a, b Value) Value {
	if a.v == nil || b.v == nil {
		return BoolVal(a.v == b.v)
	}

	// Now we've proven that both values are not nil, we'll unwrap them
	// and compare them for equality using the underlying type.
	return a.v.(Value).Equals(b.v.(Value))
}

// Null is the type of NullVal
var Null Type

// NullVal is a special value that represents the "not set" case of a maybe
// type.
var NullVal Value

type null struct {
	isTypeImpl
}

func (t null) Equals(other Type) bool {
	_, ok := other.impl.(null)
	return ok
}

func (t null) ValueEquals(a, b Value) Value {
	// All null values are equal, because there is only one concrete value
	// of this type.
	return TrueVal
}

func init() {
	Null = Type{null{}}
	NullVal = Value{
		ty: Null,
	}
}
