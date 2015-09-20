package tokenizer

//go:generate ragel -Z -G2 scanner.rl
//go:generate stringer -type=TokenKind
