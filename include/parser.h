#ifndef TOKEN_LIB
#include <token.h>
#endif

#ifndef PARSER
#define PARSER

typedef struct Parser {
    int pos;
    list* tokens;
    int listlen;
    token* value;
    int stop;
    int handleError;
    int op;
    char* ins;
    token* tk2;
    char* holder;
    list* variables;
} Parser;



token* parse(Parser* obj);

Parser* createParser(list* tokens);

void freetk(token* tk);
void alltk(token* tk);


#endif