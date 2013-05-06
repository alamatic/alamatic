
#include <boost/config/warning_disable.hpp>
#include <boost/spirit/include/lex_lexertl.hpp>
#include <boost/phoenix/bind/bind_member_function.hpp>
#include <boost/spirit/include/phoenix_operator.hpp>
#include <boost/spirit/include/phoenix_statement.hpp>
#include <boost/spirit/include/phoenix_algorithm.hpp>
#include <boost/spirit/include/phoenix_core.hpp>
#include <iostream>
#include <string>
#include <iterator>

using namespace std;
namespace lex = boost::spirit::lex;

enum TokenIds {
    TOK_INDENT = 256,
    TOK_OUTDENT,
    TOK_IDENT,
    TOK_IF,
    TOK_FOR,
    TOK_WHILE,
    TOK_FUNC,
    TOK_VAR,
    TOK_CONST,
    TOK_REQUIRE,
    TOK_ACCEPT,
    TOK_IMPORT,
    TOK_FROM,
    TOK_IN
};

template <typename Lexer>
struct alaLexer : lex::lexer<Lexer> {

  public:

    lex::token_def<std::string> ident;
    lex::token_def<> newline;
    lex::token_def<> bracket;
    lex::token_def<> space;
    lex::token_def<> keyword;
    int indent_level;
    char bracket_open_type;
    int bracket_open_count;

    alaLexer() :
        indent_level(0),
        ident("[a-zA-Z0-9_]+", TOK_IDENT),
        newline("\n *[^ ]"),
        space("[ \n]+"),
        bracket("(\\{|\\}|\\[|\\]|\\(|\\))"),
        keyword("(if|for|while|func|var|const|require|accept|import|from|in)") {

        using boost::phoenix::bind;
        using boost::phoenix::ref;

        this->bracket_open_count = 0;
        this->bracket_open_type = '\0';

        this->self = (
            keyword [bind(&alaLexer::handle_keyword, this, lex::_start, lex::_end, lex::_pass, lex::_tokenid)] |
            ident |
            newline [bind(&alaLexer::handle_leading_whitespace, this, lex::_start, lex::_end, lex::_pass, lex::_tokenid)] |
            bracket [bind(&alaLexer::handle_bracket, this, lex::_start, lex::_end, lex::_pass, lex::_tokenid)] |
            space [bind(&alaLexer::handle_whitespace, this, lex::_start, lex::_end, lex::_pass, lex::_tokenid)]
        );

    }

    void handle_keyword(const char*& start, const char*& end, BOOST_SCOPED_ENUM(lex::pass_flags)& pass, unsigned int& token_id) {

        switch (start[0]) {

            case 'f':
                switch (start[1]) {
                    case 'o':
                        token_id = TOK_FOR;
                        break;
                    case 'r':
                        token_id = TOK_FROM;
                        break;
                    case 'u':
                        token_id = TOK_FUNC;
                        break;
                }
                break;

            case 'w':
                token_id = TOK_WHILE;
                break;

            case 'v':
                token_id = TOK_VAR;
                break;

            case 'c':
                token_id = TOK_CONST;
                break;

            case 'r':
                token_id = TOK_REQUIRE;
                break;

            case 'a':
                token_id = TOK_ACCEPT;
                break;

            case 'i':
                switch (start[1]) {
                    case 'm':
                        token_id = TOK_IMPORT;
                        break;
                    case 'n':
                        token_id = TOK_IN;
                        break;
                    case 'f':
                        token_id = TOK_IF;
                        break;
                }
                break;

        }

    }


    void handle_whitespace(const char*& start, const char*& end, BOOST_SCOPED_ENUM(lex::pass_flags)& pass, unsigned int& token_id) {

        pass = lex::pass_flags::pass_ignore;

    }

    void handle_leading_whitespace(const char*& start, const char*& end, BOOST_SCOPED_ENUM(lex::pass_flags)& pass, unsigned int& token_id) {

        // If the last character is a newline then we've found a blank
        // line, which doesn't count for indentation-detecting purposes.
        if (*(end - 1) == '\n') {
            // Make the trailing newline visible for further matching.
            end--;

            // Skip this token.
            pass = lex::pass_flags::pass_ignore;

            return;
        }

        if (*(end - 1) != ' ') {
            // Back up one so we don't eat the final non-space character.
            end--;
        }

        // If we have a bracket open, treat leading whitespace just like
        // any other whitespace.
        if (this->bracket_open_count > 0) {
            pass = lex::pass_flags::pass_ignore;
            return;
        }

        int amount = end - start - 2;
        if (amount > this->indent_level) {
            this->indent_level = amount;
            token_id = TOK_INDENT;
        }
        else if (amount < this->indent_level) {
            this->indent_level = amount;
            token_id = TOK_OUTDENT;
        }
    }

    void handle_bracket(const char*& start, const char*& end, BOOST_SCOPED_ENUM(lex::pass_flags)& pass, unsigned int& token_id) {

        // We keep special track of brackets so that we can ignore
        // indents and outdents within them.

        char bracket_type = *start;
        token_id = (unsigned int) bracket_type;

        switch (bracket_type) {
            case '(':
            case '{':
            case '[':
                if (this->bracket_open_count == 0) {
                    this->bracket_open_type = bracket_type;
                }
                if (this->bracket_open_type == bracket_type) {
                    this->bracket_open_count++;
                }
                break;
            case ')':
                if (this->bracket_open_type == '(') {
                    if (--this->bracket_open_count == 0) {
                        this->bracket_open_type = '\0';
                    }
                }
                break;
            case '}':
                if (this->bracket_open_type == '{') {
                    if (--this->bracket_open_count == 0) {
                        this->bracket_open_type = '\0';
                    }
                }
                break;
            case ']':
                if (this->bracket_open_type == '[') {
                    if (--this->bracket_open_count == 0) {
                        this->bracket_open_type = '\0';
                    }
                }
                break;
        }

    }

};

