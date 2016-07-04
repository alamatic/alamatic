// temptool is a temporary tool for experimenting with the partially-completed
// Alamatic compiler. It will later be removed and replaced with a proper
// compiler driver.
package main

import (
	"os"

	"github.com/jessevdk/go-flags"
)

func main() {
	clParser := flags.NewParser(nil, flags.Default)
	clParser.AddCommand(
		"print-ast",
		"Print the AST resulting from parsing a given file",
		"The 'print-ast' command prints the AST for a given file",
		&PrintASTCommand{},
	)

	if _, err := clParser.Parse(); err != nil {
		os.Exit(1)
	}
}
