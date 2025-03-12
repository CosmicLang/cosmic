#include <token.h>
#include <lexer.h>
#include <parser.h>
#ifndef STDHD_IMP
#define STDHD_IMP
#include <stdio.h>
#include <stdlib.h>
#endif

#include <string.h>
#include <stdint.h>

char* introduction = "(C) Cosmic Open Source Community 2025\n";

int main() {
    printf(introduction);
    while (1) {
    char sd[1024];
    printf(">> ");
    list* lst = lexer(fgets(sd, 1024, stdin));
    Parser* obj = createParser(lst);
    (obj->variables) = createList();
    setv(obj->variables, "hello", Token(STRING, "hello, world", 0, 0));
    token* tk = parse(obj);
    if (tk == NULL) {
        continue;
    }
    if (tk->type == STRING) {
        printf("STRING \"%s\" ", tk->value);
    } else if (tk->type == INT) {
        printf("INTEGER (%i) ", tk->intValue);
    } else if (tk->type == FLOAT) {
        printf("FLOAT (%f) ", tk->doubleValue);
    } else if(tk->type == IDENTIFIER) {
        printf("VARIABLE %s ", tk->value);
    }  
    printf("\n");
    }  
  
};