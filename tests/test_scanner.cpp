
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
            blah4
                blah5
            blah6
    blah7
)";

    ExpectedToken expected[] = {
        { TOK_IDENT, "blah1" },
        { TOK_INDENT, "    " },
        { TOK_IDENT, "blah2" },
        { TOK_INDENT, "        " },
        { TOK_IDENT, "blah3" },
        { TOK_INDENT, "            " },
        { TOK_IDENT, "blah4" },
        { TOK_INDENT, "                " },
        { TOK_IDENT, "blah5" },
        { TOK_OUTDENT, "" },
        { TOK_IDENT, "blah6" },
        { TOK_OUTDENT, "" },
        { TOK_OUTDENT, "" },
        { TOK_IDENT, "blah7" },
        { TOK_OUTDENT, "" },
        { 0, 0 }
    };

    ASSERT_TRUE(test_scanner(test, expected));
}
