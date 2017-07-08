package aty

// Bool is a type representing boolean values. The only values of this type
// are TrueVal and FalseVal.
var Bool Type

// TrueVal is the true value of type Bool
var TrueVal Value

// FalseVal is the false value of type Bool
var FalseVal Value

// BoolVal converts a native Go bool value into an aty Bool value.
func BoolVal(v bool) Value {
	return Value{
		ty: Bool,
		v:  v,
	}
}

type bool_ struct {
	isTypeImpl
}

func (t bool_) Equals(other Type) bool {
	_, ok := other.impl.(bool_)
	return ok
}

func (t bool_) ValueEquals(a, b Value) Value {
	return BoolVal(a.v.(bool) == b.v.(bool))
}

func init() {
	Bool = Type{bool_{}}

	TrueVal = Value{
		ty: Bool,
		v:  true,
	}
	FalseVal = Value{
		ty: Bool,
		v:  false,
	}
}
