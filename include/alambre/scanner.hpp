
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
#include <stack>

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

struct BracketOpen {
    char type;
    int count;
};

struct ScannerState {
    std::stack<int> indents;
    BracketOpen bracket_open;
};

class handle_indentation {
  public:
    ScannerState& state;

    handle_indentation(ScannerState& state_) : state(state_) {}

    template <typename Iterator, typename IdType, typename Context>
    void operator()(Iterator& start, Iterator& end, BOOST_SCOPED_ENUM(lex::pass_flags)& pass, IdType& token_id, Context& ctx) {

        // If the last character is a newline then we've found a blank
        // line, which doesn't count for indentation-detecting purposes.
        if (*(end - 1) == '\n') {
            // Make the trailing newline visible for further matching.
            end--;

            // Skip this token.
            pass = lex::pass_flags::pass_ignore;

            ctx.set_state_name("MAIN");
            return;
        }

        if (*(end - 1) != ' ') {
            // Back up one so we don't eat the final non-space character.
            end--;
        }

        // If we have a bracket open, treat leading whitespace just like
        // any other whitespace.
        if (this->state.bracket_open.count > 0) {
            pass = lex::pass_flags::pass_ignore;
            ctx.set_state_name("MAIN");
            return;
        }

        int next = std::distance(start, end);
        int current = this->state.indents.top();
        if (next == current) {
            pass = lex::pass_flags::pass_ignore;
        }
        else if (next > current) {
            this->state.indents.push(next);
            token_id = TOK_INDENT;
        }
        else {
            this->state.indents.pop();
            int previous = this->state.indents.top();
            if (next > previous) {
                // FIXME: This should actually fail the entire
                // lexing process, but it actually ends up just skipping
                // the current token. At the very least we should actually
                // emit an error here so we don't end up raising a dumb
                // error at parse time.
                pass = lex::pass_flags::pass_fail;
            }
            else {
                token_id = TOK_OUTDENT;
                // force a re-read of this token now that we've popped
                // the stack... this way we'll keep generating OUTDENT
                // tokens until we're lined up with an earlier indent.
                end = start;
                // We intentionally don't switch back to MAIN in this case,
                // because we want to keep matching the same whitespace.
                return;
            }
        }

        ctx.set_state_name("MAIN");

    }
};

class handle_newline {
  public:
    ScannerState& state;

    handle_newline(ScannerState& state_) : state(state_) {}

    template <typename Iterator, typename IdType, typename Context>
    void operator()(Iterator& start, Iterator& end, BOOST_SCOPED_ENUM(lex::pass_flags)& pass, IdType& token_id, Context& ctx) {

        // If we've reached the end of the input, pop off all of the open
        // indents before we finish.
        // FIXME: Doing this here means that we fail in a weird way if the
        // input doesn't end with a newline, because the OUTDENT tokens
        // never get emitted.
        if (end == ctx.get_eoi()) {
            // Pop off all of the open indents before we finish.
            if (this->state.indents.top() > 0) {
                this->state.indents.pop();
                // Reset the end so we'll re-parse this final newline
                // repeatedly until the indents stack is empty.
                end = start;
                token_id = TOK_OUTDENT;
                return;
            }
        }

        pass = lex::pass_flags::pass_ignore;
        ctx.set_state_name("INITIAL");

    }
};

template <typename Lexer>
struct alaLexer : lex::lexer<Lexer> {

  public:

    lex::token_def<> indentation;
    lex::token_def<std::string> ident;
    lex::token_def<> newline;
    lex::token_def<> bracket;
    lex::token_def<> space;
    lex::token_def<> keyword;
    ScannerState state;

    alaLexer() :
        indentation(" *[^ ]"),
        ident("[a-zA-Z0-9_]+", TOK_IDENT),
        newline("\n"),
        space(" +"),
        bracket("(\\{|\\}|\\[|\\]|\\(|\\))"),
        keyword("(accept|const|for|from|func|if|import|in|require|var|while)") {

        using boost::phoenix::bind;
        using boost::phoenix::ref;

        // No brackets open initially, of course.
        this->state.bracket_open.count = 0;
        this->state.bracket_open.type = '\0';
        // We always start at indent position zero.
        this->state.indents.push(0);

        // The INITIAL state is the indentation-detecting state, where we'll
        // slurp up any initial whitespace, handle any indentation changes, and
        // then switch to the MAIN state defined below, where the interesting
        // stuff happens.
        this->self = (
            indentation [handle_indentation(this->state)]
        );

        // The MAIN state is where we recognize a line of "visible" language
        // tokens, switching back to the INITIAL state when we reach the
        // end of the line.
        this->self("MAIN") = (
            keyword [bind(&alaLexer::handle_keyword, this, lex::_start, lex::_end, lex::_pass, lex::_tokenid)] |
            ident |
            newline [handle_newline(this->state)] |
            bracket [bind(&alaLexer::handle_bracket, this, lex::_start, lex::_end, lex::_pass, lex::_tokenid)] |
            space [bind(&alaLexer::handle_whitespace, this, lex::_start, lex::_end, lex::_pass, lex::_tokenid)]
        );

    }

    void handle_keyword(const char*& start, const char*& end, BOOST_SCOPED_ENUM(lex::pass_flags)& pass, unsigned int& token_id) {

        switch (start[0]) {

            case 'a':
                token_id = TOK_ACCEPT;
                break;

            case 'c':
                token_id = TOK_CONST;
                break;

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

            case 'r':
                token_id = TOK_REQUIRE;
                break;

            case 'v':
                token_id = TOK_VAR;
                break;

            case 'w':
                token_id = TOK_WHILE;
                break;

        }

    }

    void handle_whitespace(const char*& start, const char*& end, BOOST_SCOPED_ENUM(lex::pass_flags)& pass, unsigned int& token_id) {

        pass = lex::pass_flags::pass_ignore;

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
                if (this->state.bracket_open.count == 0) {
                    this->state.bracket_open.type = bracket_type;
                }
                if (this->state.bracket_open.type == bracket_type) {
                    this->state.bracket_open.count++;
                }
                break;
            case ')':
                if (this->state.bracket_open.type == '(') {
                    if (--this->state.bracket_open.count == 0) {
                        this->state.bracket_open.type = '\0';
                    }
                }
                break;
            case '}':
                if (this->state.bracket_open.type == '{') {
                    if (--this->state.bracket_open.count == 0) {
                        this->state.bracket_open.type = '\0';
                    }
                }
                break;
            case ']':
                if (this->state.bracket_open.type == '[') {
                    if (--this->state.bracket_open.count == 0) {
                        this->state.bracket_open.type = '\0';
                    }
                }
                break;
        }

    }

};
