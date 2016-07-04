package main

import (
	"fmt"
	"io/ioutil"

	"github.com/alamatic/alamatic/ast"
	"github.com/alamatic/alamatic/tokenizer"
)

type PrintASTCommand struct {
	Args PrintASTArgs `positional-args:"true" required:"true"`
}

type PrintASTArgs struct {
	SourceFilename string `positional-arg-name:"filename" required:"true"`
}

func (c *PrintASTCommand) Execute(args []string) error {
	source, err := ioutil.ReadFile(c.Args.SourceFilename)
	if err != nil {
		return err
	}

	tokens := tokenizer.Tokenize(source, c.Args.SourceFilename)
	m := ast.ParseModule(tokens)

	fmt.Printf("module %#v\n", m)

	return nil
}
