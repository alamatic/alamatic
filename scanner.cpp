
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
    TOK_OUTDENT
};

template <typename Lexer>
struct alaLexer : lex::lexer<Lexer> {

  public:

    lex::token_def<std::string> ident;
    lex::token_def<> newline;
    int indent_level;

    alaLexer() : indent_level(0), ident("[a-zA-Z0-9_]+"), newline("\n *[^ ]") {

        using boost::phoenix::bind;

        this->self = (
            ident |
            //newline [cout << "Whitespace from " << lex::_start << " to " << lex::_end << "\n"]
            newline [bind(&alaLexer::handle_whitespace, this, lex::_start, lex::_end, lex::_pass, lex::_tokenid)]
        );

    }

    void handle_whitespace(const char*& start, const char*& end, lex::pass_flags::enum_type& pass, unsigned int& token_id) {

        // If the last character is a newline then we've found a blank
        // line, which doesn't count for indentation-detecting purposes.
        if (*(end - 1) == '\n') {
            // Make the trailing newline visible for further matching.
            end--;

            // Skip this token.
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
        // Back up one so we don't eat the final character.
        end--;
    }

};

int main(int argc, char **argv) {

    typedef lex::lexertl::token<char const*> token_type;
    typedef lex::lexertl::actor_lexer<token_type> lexer_type;

    alaLexer<lexer_type> lexer;

    std::string str("hello\n    hello\n\n    hello\nhello\n");
    char const* first = str.c_str();
    char const* last = &first[str.size()];

    lexer_type::iterator_type iter = lexer.begin(first, last);
    lexer_type::iterator_type end = lexer.end();

    while (iter != end && token_is_valid(*iter)) {
        if ((*iter).id() == lexer.ident.id()) {
            cout << "Ident: " << (*iter).value() << "\n";
        }
        if ((*iter).id() == TOK_INDENT) {
            cout << "Indent\n";
        }
        if ((*iter).id() == TOK_OUTDENT) {
            cout << "Outdent\n";
        }
        ++iter;
    }

    

}

