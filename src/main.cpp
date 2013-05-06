
#include <alambre/scanner.hpp>

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
