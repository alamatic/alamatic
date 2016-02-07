/*
Package tokenizer provides a tokenizer for source files for the Alamatic
programming language.

The goal of the tokenizer is to transform a stream of bytes representing the
source code into a stream of lexical tokens that will be the input into the
Alamatic parser.

The tokenizer is split into two parts: the scanner does basic token
classification, and then the tokenizer processes the raw token stream
adjusts the raw token stream to prepare it for parsing.

The scanner, whose entry point is the function Scan, guarantees to group and
classify each byte in the source file into exactly one token. The scanning
process is loss-less in that all source file bytes appear in the same order
in the token stream. The byte slices in tokens are sub-slices of the original
source file buffer provided to Scan.

The tokenizer, whose entry point is Tokenize, returns a token stream that
has been stripped of raw whitespace and comments, and contains synthetic
INDENT and OUTDENT tokens representing the blocks implied by changes
of indentation. The tokenization process is lossy in that not all source
bytes are preserved.

Most callers will interact with the tokenizer as part of preparing a source
file for parsing, but the low-level scanner can be useful for implementing
the simple token classification required for a syntax highlighting lexer.

A token stream is a read-only channel of Token. Parsing Alamatic source
requires one token lookahead, so the TokenPeeker utility wraps a Token
channel (either a raw or raised stream) and provides Peek and Read functions
that make parsing more convienient, along with a utility to assist in creating
source ranges for inclusion in diagnostics.

*/
package tokenizer
