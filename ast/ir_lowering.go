package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type SymbolMaker func(string, *diag.SourceRange) Symbol

type Scope struct {
	Symbols       map[string]Symbol
	Parent        *Scope
	ContinueBlock *ir.BasicBlock
	BreakBlock    *ir.BasicBlock
	MakeVariable  SymbolMaker
	MakeConstant  SymbolMaker
}

func NewScope() *Scope {
	return &Scope{
		Symbols: map[string]Symbol{},
	}
}

func (s *Scope) NewChild() *Scope {
	newScope := NewScope()
	newScope.Parent = s

	// By default we use all the same context as the parent.
	// The caller can override these if the context is changing.
	newScope.ContinueBlock = s.ContinueBlock
	newScope.BreakBlock = s.BreakBlock
	newScope.MakeVariable = s.MakeVariable
	newScope.MakeConstant = s.MakeConstant

	return newScope
}

func (s *Scope) DeclareVariable(name string, declRange *diag.SourceRange) Symbol {
	v := s.MakeVariable(name, declRange)
	s.Symbols[name] = v
	return v
}

func (s *Scope) DeclareConstant(name string, declRange *diag.SourceRange) Symbol {
	v := s.MakeConstant(name, declRange)
	s.Symbols[name] = v
	return v
}

func (s *Scope) Symbol(name string) Symbol {
	current := s
	for current != nil {
		if sym, ok := current.Symbols[name]; ok {
			return sym
		}
		current = current.Parent
	}
	return nil
}

type Symbol interface {
	DeclName() string
	DeclRange() *diag.SourceRange
}
