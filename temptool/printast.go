package main

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"reflect"

	"github.com/alamatic/alamatic/ast"
	"github.com/alamatic/alamatic/tokenizer"
)

var indentBytes = [...]byte{' ', ' ', ' ', ' '}

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

	c.printASTNode(m, os.Stdout, 0)
	return nil
}

func (c *PrintASTCommand) printASTNode(n ast.ASTNode, w io.Writer, indent int) {

	for i := 0; i < indent; i++ {
		w.Write(indentBytes[:])
	}

	nodeType := reflect.TypeOf(n).Elem()
	w.Write([]byte(nodeType.Name()))

	params := n.Params()
	first := true
	w.Write([]byte{'('})
	for _, param := range params {
		if first {
			first = false
		} else {
			w.Write([]byte{',', ' '})
		}

		fmt.Fprintf(w, "%#v", param)
	}
	w.Write([]byte{')'})

	childNodes := n.ChildNodes()
	if childNodes == nil || len(childNodes) == 0 {
		w.Write([]byte{'\n'})
		return
	}

	w.Write([]byte{':', '\n'})

	for _, childNode := range childNodes {
		c.printASTNode(childNode, w, indent+1)
	}
}
