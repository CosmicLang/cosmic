#include <lexer.h>
#ifndef TOKEN_LIB
#include <token.h>
#endif
#ifndef STDHD_IMP
#define STDHD_IMP
#include <stdio.h>
#include <stdlib.h>
#endif

#include <string.h>



list* lexer(char* string) {
    int pos = 0;
    list* tokens = createList();
    int line = 1;
    int lsl = 0;
    int lxlength = strlen(string);
    while (string[pos] > lxlength) {
        char chr = string[pos];
        if (chr == ' ' || chr == '\t' || chr == '\n') {
            if (chr == '\n') {
                lsl = pos;
                line++;
            }
        } else if (chr == '+' || chr == '-' || chr == '/' || chr == '*') {
            switch((int)chr) {
                case '+': {
                    addItem(tokens, (char*)Token(PLUS, NULL, pos-lsl, line));
                    break;
                };
                case '-': {
                    addItem(tokens, (char*)Token(MINUS, NULL, pos-lsl, line));
                    break;
                };
                case '*': {
                    addItem(tokens, (char*)Token(MULTIPLY, NULL, pos-lsl, line));
                    break;
                };
                case '/': {
                    addItem(tokens, (char*)Token(DIVIDE, NULL, pos-lsl, line));
                    break;
                };
            }
        } else if (chr == '\"') {
            int start_pos = pos;
            int length = 0;
            int start_line = line;
            while (string[pos+1] != '\"') {
                pos++;
                length++;
                if (string[pos] == '\n') {
                    lsl = pos;
                    line++;
                }
                if (string[pos] == '\0') {
                    error("StringError", "Unterminated string", line, start_pos - lsl);
                }
            }
            pos++;
            char* new_str = malloc(length + 1);
            int ils = 0;
            while (ils != length) {
                new_str[ils] = string[start_pos + ils + 1];
                ils++;
            }
            token* tk = Token(STRING, new_str, start_pos, start_line);
            addItem(tokens, (char*)tk);
        } else if (chr == '\'') {
            int start_pos = pos;
            int length = 0;
            int start_line = line;
            while (string[pos+1] != '\'') {
                pos++;
                length++;
                if (string[pos] == '\n') {
                    line++;
                    lsl = pos;
                }
                if (string[pos] == '\0') {
                    error("StringError", "Unterminated string", line, start_pos - lsl);
                }
            }
            pos++;
            char* new_str = malloc(length + 1);
            int ils = 0;
            while (ils != length) {
                new_str[ils] = string[start_pos + ils + 1];
                ils++;
            }
            token* tk = Token(STRING, new_str, start_pos, start_line);
            addItem(tokens, (char*)tk);
        } else if (chr >= '0' && chr <= '9') {
            int num = chr - '0';
            int start_pos = 0;
            while (string[pos+1] >= '0' && string[pos+1] <= '9') {
                pos++;
                num = (num*10) + (string[pos] - '0');
            }
            int ntype = INT;
            int dec = 0;
            double loc = 0.1;
            double flt = 0.0;

            if(string[pos+1] == '.') {
                dec = 1;
            }
            if (dec == 1) {
                pos++;
                while (string[pos+1] >= '0' && string[pos+1] <= '9') {
                    pos++;
                    flt = flt + (loc * (string[pos]-'0'));
                    loc = loc * 0.1;

                }
                if (string[pos+1] == '.') {
                        error("FloatError", "Detected Another Decimal point", line, (pos - lsl)+1);
                }
                token* tk = Token(FLOAT, NULL, pos-lsl, line);
                tk->doubleValue = flt + (double)(num);
                addItem(tokens, (char*)tk);
            } else {
                token* tk = Token(INT, NULL, pos-lsl, line);
                tk->intValue = num;
                addItem(tokens, (char*)tk);
            }
        } else if (chr == '.') {
            double flt = 0.0;
            double loc = 0.1;
            while (string[pos+1] >= '0' && string[pos+1] <= '9') {
                pos++;
                flt = flt + (loc * (string[pos]-'0'));
                loc = loc * 0.1;
            }
            token* tk = Token(FLOAT, NULL, pos-lsl, line);
            tk->doubleValue = flt;
            addItem(tokens, (char*)tk);

        } else if (chr == '(') {
                token* tk = Token(L_PAREN, NULL, pos-lsl, line);
                addItem(tokens, (char*)tk);
        } else if (chr == ')') {
                token* tk = Token(R_PAREN, NULL, pos-lsl, line);
                addItem(tokens, (char*)tk);
        } else if (chr == '[') {
                token* tk = Token(L_BRACKET, NULL, pos-lsl, line);
                addItem(tokens, (char*)tk);
        } else if (chr == ']') {
                token* tk = Token(R_BRACKET, NULL, pos-lsl, line);
                addItem(tokens, (char*)tk);
        } else if (chr == '{') {
                token* tk = Token(L_BRACE, NULL, pos-lsl, line);
                addItem(tokens, (char*)tk);
        } else if (chr == '}') {
                token* tk = Token(R_BRACE, NULL, pos-lsl, line);
                addItem(tokens, (char*)tk);
        } else if (chr == ',') {
                token* tk = Token(COLON, NULL, pos-lsl, line);
                addItem(tokens, (char*)tk);
        } else if (chr == ';') {
                token* tk = Token(SEMICOLON, NULL, pos-lsl, line);
                addItem(tokens, (char*)tk);
        } else if (chr == '=') {
            if (string[pos+1] == '=') {
                    token* tk = Token(EQUAL, NULL, pos-lsl, line);
                    addItem(tokens, (char*)tk);
            } else {
                    token* tk = Token(ASSIGN, NULL, pos-lsl, line);
                    addItem(tokens, (char*)tk);
            }
        } else if (chr == '!') {
            if (string[pos+1] == '=') {
                    token* tk = Token(NOT_EQUAL, NULL, pos-lsl, line);
                    addItem(tokens, (char*)tk);
            } else {
                    error("SyntaxError", "no '=' sign after '!'", line, pos-lsl);
            }
        } else if (chr == '>') {
            if (string[pos+1] == '=') {
                    token* tk = Token(GREATER_EQUAL, NULL, pos-lsl, line);
                    addItem(tokens, (char*)tk);
            } else {
                    token* tk = Token(GREATER, NULL, pos-lsl, line);
                    addItem(tokens, (char*)tk);
            }
        } else if (chr == '<') {
            if (string[pos+1] == '=') {
                    token* tk = Token(LESSER_EQUAL, NULL, pos-lsl, line);
                    addItem(tokens, (char*)tk);
            } else {
                    token* tk = Token(LESSER, NULL, pos-lsl, line);
                    addItem(tokens, (char*)tk);
            }
        } else if ((chr >= 'a' && chr <= 'z') || (chr >= 'A' && chr <= 'Z') || (chr == '_')) {
            char* start_pos = string + pos;
            int length = 1;
            chr = string[pos+1];
            while ((chr >= 'a' && chr <= 'z') || (chr >= 'A' && chr <= 'Z') || (chr == '_') || ((chr >= '0') && (chr <= '9'))) {
                length++;
                pos++;
                chr = string[pos+1];
            }
            char* id = malloc(length+1);
            id[length] = 0;
            int i = 0;
            while (i < length) {
                id[i] = start_pos[i];
                i++;
            };
            token* tk = Token(IDENTIFIER, id, pos-lsl, line);
            addItem(tokens, (char*)tk);
        } else {
            char* ipo = "invalid character 'x'.";
            ipo[19] = chr;
            error("SyntaxError", ipo, line, pos-lsl);
        };
        pos++;
    }
    return tokens;
}