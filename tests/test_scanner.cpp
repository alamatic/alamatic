
#include <alambre/scanner.hpp>
#include "gtest/gtest.h"
#include <stdio.h>
#include <string.h>
#include <string>
#include <iostream>

struct ExpectedToken {
    unsigned int id;
    const char * value;
};


::testing::AssertionResult test_scanner(const char * input, ExpectedToken *expected_tokens) {
    typedef lex::lexertl::token<char const*> token_type;
    typedef lex::lexertl::actor_lexer<token_type> lexer_type;

    alaLexer<lexer_type> lexer;

    char const* first = input;
    char const* last = &first[strlen(input)];

    lexer_type::iterator_type iter = lexer.begin(first, last);
    lexer_type::iterator_type end = lexer.end();

    ExpectedToken * expected = expected_tokens;

    while (iter != end && token_is_valid(*iter)) {
        unsigned int got_id = (*iter).id();
        unsigned int expected_id = expected->id;
        std::string got_value((*iter).value().begin(), (*iter).value().end());

        if (expected_id == 0) {
            return ::testing::AssertionFailure() << "Unexpected extra token with id " << got_id << " and value " << got_value;
        }

        std::string expected_value(expected->value);

        if (got_id != expected_id) {
            return ::testing::AssertionFailure() << "Expected token " << expected_id << " (with " << expected_value << ") but got token " << got_id << " (with " << got_value << ")";
        }

        if (got_value != expected_value) {
            return ::testing::AssertionFailure() << "For token " << got_id << ", expected value " << expected_value << " but got " << got_value;
        }

        ++iter;
        ++expected;
    }

    if (expected->id != 0) {
        return ::testing::AssertionFailure() << "Unexpected EOF (was expecting " << expected->id << " with value " << expected->value << ")";
    }

    return ::testing::AssertionSuccess();
}

// Just a simple test to start with.
TEST(TestScanner, IfKeyword) {
    const char * test = "if";

    ExpectedToken expected[] = {
        { TOK_IF, "if" },
        { 0, 0 }
    };

    ASSERT_TRUE(test_scanner(test, expected));
}

TEST(TestScanner, IndentOutdent) {
    const char * test = R"(blah1
    blah2
        blah3
        blah3a
            blah4
                blah5
            blah6
    blah7
)";

    ExpectedToken expected[] = {
        { TOK_IDENT, "blah1" },
        { TOK_INDENT, "" },
        { TOK_IDENT, "blah2" },
        { TOK_INDENT, "" },
        { TOK_IDENT, "blah3" },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah3a" },
        { TOK_INDENT, "" },
        { TOK_IDENT, "blah4" },
        { TOK_INDENT, "" },
        { TOK_IDENT, "blah5" },
        { TOK_OUTDENT, "" },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah6" },
        { TOK_OUTDENT, "" },
        { TOK_OUTDENT, "" },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah7" },
        { TOK_OUTDENT, "" },
        { TOK_NEWLINE, "" },
        { 0, 0 }
    };

    ASSERT_TRUE(test_scanner(test, expected));
}

TEST(TestScanner, Brackets) {
    // Tests that we don't get indent, outdent and newline tokens
    // while inside brackets.

    const char * test = R"(blah1 {
    blah2
} blah3
blah4 (
    {blah5}
    blah6
) blah7 [
    blah8
]
blah9
)";

    ExpectedToken expected[] = {
        { TOK_IDENT, "blah1" },
        { '{', "{" },
        { TOK_IDENT, "blah2" },
        { '}', "}" },
        { TOK_IDENT, "blah3" },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah4" },
        { '(', "(" },
        { '{', "{" },
        { TOK_IDENT, "blah5" },
        { '}', "}" },
        { TOK_IDENT, "blah6" },
        { ')', ")" },
        { TOK_IDENT, "blah7" },
        { '[', "[" },
        { TOK_IDENT, "blah8" },
        { ']', "]" },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah9" },
        { TOK_NEWLINE, "" },
        { 0, 0 }
    };

    ASSERT_TRUE(test_scanner(test, expected));
}

TEST(TestScanner, Comments) {

    const char * test = R"(
# this is a plain old comment that should be ignored (including these brackets)
blah1

#: this is a single-line doc comment
blah2

#: this is a multi-line doc comment
#: that should appear as three separate
#: tokens in the token stream.
blah3

blah4 # this is an end-of-line comment

blah5 #: this is an end-of-line doc comment

blah6
)";

    ExpectedToken expected[] = {
        { TOK_NEWLINE, "" }, // comment is ignored but still generates newline
        { TOK_IDENT, "blah1" },
        { TOK_NEWLINE, "" },
        { TOK_DOC_COMMENT, " this is a single-line doc comment" },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah2" },
        { TOK_NEWLINE, "" },
        { TOK_DOC_COMMENT, " this is a multi-line doc comment" },
        { TOK_NEWLINE, "" },
        { TOK_DOC_COMMENT, " that should appear as three separate" },
        { TOK_NEWLINE, "" },
        { TOK_DOC_COMMENT, " tokens in the token stream." },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah3" },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah4" },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah5" },
        { TOK_DOC_COMMENT, " this is an end-of-line doc comment" },
        { TOK_NEWLINE, "" },
        { TOK_IDENT, "blah6" },
        { TOK_NEWLINE, "" },
        { 0, 0 }
    };

    ASSERT_TRUE(test_scanner(test, expected));
}

TEST(TestScanner, Punctuation) {

    const char * test = ": = , | & ^ == != < <= > >= * / % ~ - +\n";

    ExpectedToken expected[] = {
        { TOK_COLON, ":" },
        { TOK_ASSIGN, "=" },
        { TOK_COMMA, "," },
        { TOK_BITWISE_OR, "|" },
        { TOK_BITWISE_AND, "&" },
        { TOK_BITWISE_XOR, "^" },
        { TOK_EQUAL, "==" },
        { TOK_NOT_EQUAL, "!=" },
        { TOK_LESS_THAN, "<" },
        { TOK_LESS_THAN_EQUAL, "<=" },
        { TOK_GREATER_THAN, ">" },
        { TOK_GREATER_THAN_EQUAL, ">=" },
        { TOK_STAR, "*" },
        { TOK_SLASH, "/" },
        { TOK_PERCENT, "%" },
        { TOK_BITWISE_NOT, "~" },
        { TOK_MINUS, "-" },
        { TOK_PLUS, "+" },
        { TOK_NEWLINE, "" },
        { 0, 0 }
    };

    ASSERT_TRUE(test_scanner(test, expected));

    ASSERT_TRUE(! (TOK_COLON & TOK_TYPE_OP));
    ASSERT_TRUE(! (TOK_ASSIGN & TOK_TYPE_OP));
    ASSERT_TRUE(! (TOK_COMMA & TOK_TYPE_OP));
    ASSERT_TRUE(TOK_BITWISE_OR & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_BITWISE_AND & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_BITWISE_XOR & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_EQUAL & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_NOT_EQUAL & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_LESS_THAN & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_LESS_THAN_EQUAL & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_GREATER_THAN & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_GREATER_THAN_EQUAL & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_STAR & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_SLASH & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_PERCENT & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_BITWISE_NOT & TOK_TYPE_UNARY_OP);
    ASSERT_TRUE(TOK_MINUS & TOK_TYPE_BOTH_OP);
    ASSERT_TRUE(TOK_PLUS & TOK_TYPE_BOTH_OP);
    ASSERT_TRUE(TOK_TYPE_OP & TOK_TYPE_BINARY_OP);
    ASSERT_TRUE(TOK_TYPE_OP & TOK_TYPE_UNARY_OP);
    ASSERT_TRUE(TOK_TYPE_OP & TOK_TYPE_BOTH_OP);
    ASSERT_TRUE((TOK_TYPE_BINARY_OP & TOK_TYPE_UNARY_OP) == TOK_TYPE_OP);
    ASSERT_TRUE((TOK_TYPE_BINARY_OP | TOK_TYPE_UNARY_OP) == TOK_TYPE_BOTH_OP);

}
