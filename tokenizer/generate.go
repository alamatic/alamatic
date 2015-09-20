package tokenizer

//go:generate ragel -Z -G1 scanner.rl
//go:generate stringer -type=TokenKind
