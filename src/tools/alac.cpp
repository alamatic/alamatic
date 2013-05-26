
#include <alamatic/scanner.hpp>

int main(int argc, char **argv) {

    typedef lex::lexertl::token<char const*> token_type;
    typedef lex::lexertl::actor_lexer<token_type> lexer_type;

    alaLexer<lexer_type> lexer;

    std::string str("hello\n    hello\n\n    hello\nif hello {\n    hello\n}\n");
    char const* first = str.c_str();
    char const* last = &first[str.size()];

    lexer_type::iterator_type iter = lexer.begin(first, last);
    lexer_type::iterator_type end = lexer.end();

    while (iter != end && token_is_valid(*iter)) {
        unsigned int token_id = (*iter).id();
        switch (token_id) {
            case TOK_IDENT:
                cout << "Ident: " << (*iter).value() << "\n";
                break;
            case TOK_INDENT:
                cout << "Indent\n";
                break;
            case TOK_OUTDENT:
                cout << "Outdent\n";
                break;
            default:
                if (token_id < 128) {
                    cout << "Punctuation: " << (*iter).value() << "\n";
                }
                else {
                    cout << "Token type " << token_id << ": " << (*iter).value() << "\n";
                }
        }
        ++iter;
    }

    if (iter != end) {
        cout << "Something went wrong :(\n";
    }

}
