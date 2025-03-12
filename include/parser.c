#include <token.h>
#include <parser.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef NULL
#define NULL (void*)(0)
#endif


void freetk(token* tk) {
    if (tk != NULL) {
        tk->ref--;
        if (tk->ref != 0) {
            return;
        }
        if (tk->value != NULL) {
            free(tk->value);
        }
        free(tk);
    }
}

void alltk(token* tk) {
    tk->ref++;
}

char* concat(char* dst, char* src) {
    char* new = malloc(strlen(dst) + strlen(src) + 1);
    new[(strlen(dst) + strlen(src)) - 1] = 0;
    int i = 0;
    int p = 0;
    while (i < strlen(dst)) {
        new[p] = dst[i];
        i++;
        p++;
    }
    i = 0;
    while (i < strlen(src)) {
        new[p] = src[i];
        i++;
        p++;
    }
    return new;
}

Parser* createParser(list* tokens) {
    Parser* obj = malloc(sizeof(Parser));
    obj->tokens = tokens;
    obj->listlen = listlen(tokens);
    obj->pos=0;
    obj->value = NULL;
    obj->op = NO_OP;
    obj->stop = SEMICOLON;
    return obj;
}

char* nam(int v) {
    if (v == INT) {
        return "integer";
    }
    if (v == FLOAT) {
        return "float";
    }
    if (v == STRING) {
        return "string";
    }
    if (v == EQUAL) {
        return "equal";
    }
    if (v == NOT_EQUAL) {
        return "not equal";
    }
    if (v == GREATER) {
        return "greater";
    }
    if (v == GREATER_EQUAL) {
        return "greater or equal";
    }
    if (v == LESSER) {
        return "lesser";
    }
    if (v == LESSER_EQUAL) {
        return "lesser or equal";
    }
    if (v == PLUS) {
        return "plus";
    }
    if (v == MINUS) {
        return "minus";
    }
    if (v == DIVIDE) {
        return "divide";
    }
    if (v == MULTIPLY) {
        return "multiply";
    }
}





token* parse(Parser* obj) {
    obj->value = NULL;
    obj->op = NO_OP;
    while(obj->pos < obj->listlen) {
        token* tk = (token*)getItem(obj->tokens, obj->pos);
        if (tk->type == obj->stop) {
            freetk(tk);
            return obj->value;
        } else if ((tk->type == IDENTIFIER) && ((obj->pos+1) < obj->listlen) && (((token*)getItem(obj->tokens, obj->pos+1))->type == L_PAREN)) {
            obj->holder = tk->value;

            freetk(tk);
            freetk((token*)getItem(obj->tokens, obj->pos+1));
            obj->pos++;
            obj->ins = (char*)createParser(split_tt(obj->tokens, obj->pos+1));
            ((Parser*)obj->ins)->stop = R_PAREN;
            obj->tk2 = parse((Parser*)obj->ins);
            token* tker = Token(0, NULL, ((token*)getItem(obj->tokens, obj->pos-1))->pos, ((token*)getItem(obj->tokens, obj->pos-1))->line);

            if ((cmps(obj->holder, "toInt") == 0) || (cmps(obj->holder, "Integer") == 0) || (cmps(obj->holder, "Int") == 0) || (cmps(obj->holder, "int") == 0) || (cmps(obj->holder, "integer") == 0)) {
                if (obj->tk2->type == STRING) {
                    int lengtho = strlen(obj->tk2->value);
                    char* string = obj->tk2->value;
                    int posso = 0;
                    int num;
                    int already_num = 0;
                    while (posso < lengtho) {
                        char chr = string[posso];
                        int line = 1;
                        int lsl = 0;

                        if (chr == '\n') {
                            line++;
                            lsl = posso;
                        } if ((chr == ' ') || (chr == '\t')) {
                        } else if (chr >= '0' && chr <= '9') {
                            if (already_num == 1) {
                                error("SyntaxError", "already got a number at int conversion.", line, posso-lsl);
                            }
                            num = chr - '0';
                            int start_pos = 0;
                            while (string[posso+1] >= '0' && string[posso+1] <= '9') {
                                posso++;
                                num = (num*10) + (string[posso] - '0');
                            }
                            int ntype = INT;
                            int dec = 0;
                            double loc = 0.1;
                            double flt = 0.0;
                            if(string[posso+1] == '.') {
                                dec = 1;
                            }
                            if (dec == 1) {
                                posso++;
                                while (string[posso+1] >= '0' && string[posso+1] <= '9') {
                                    posso++;
                                    flt = flt + (loc * (string[posso]-'0'));
                                    loc = loc * 0.1;

                                }
                                if (string[posso+1] == '.') {
                                        error("FloatError", "Detected Another Decimal point, while doing int conversion.", line, (posso - lsl)+1);
                                }
                            }
                        }
                        else {
                            char* ipo = "invalid character 'x' inside int conversion.";
                            ipo[19] = chr;
                            error("SyntaxError", ipo, line, posso-lsl);
                        };
                        posso++;
                    }
                    freetk(obj->tk2);
                    tker->type = INT;
                    tker->intValue = num;
                } else if (obj->tk2->type == INT) {
                    tker->type = INT;
                    tker->intValue = obj->tk2->intValue;
                    freetk(obj->tk2);
                } else if (obj->tk2->type == FLOAT) {
                    tker->type = INT;
                    tker->intValue = (int)(obj->tk2->doubleValue);
                    freetk(obj->tk2);
                } else {
                    error("TypeError", "expected float, string or integer for int conversion", obj->tk2->line, obj->tk2->pos);
                    freetk(obj->tk2);
                }
            }
            obj->pos = (((Parser*)obj->ins)->pos + obj->pos);
            setItem(obj->tokens, obj->pos, (char*)tker);
            obj->pos-=1;
            free(obj->ins);
        } else if ((tk->type == INT) || (tk->type==FLOAT)) {
            if (obj->op == NO_OP) {
                obj->value = tk;
            } else {
                double val1, val2;
                if (obj->value->type == INT) {
                    val1 = (double)obj->value->intValue;
                } else if (obj->value->type == FLOAT) {
                    val1 = obj->value->doubleValue;
                } else {
                    char* err = "Cannot do operations on type '";
                    char* errc = concat(err, nam(obj->value->type));
                    err = errc;
                    errc = concat(err, "' with type '");
                    free(err);
                    err = errc;
                    errc = concat(err, nam(tk->type));
                    free(err);
                    err = errc;
                    errc = concat(err, "'");
                    free(err);
                    error("OperationError", errc, tk->line, tk->pos);
                    free(errc);
                }
                if (tk->type == INT) {
                    val2 = (double)tk->intValue;
                    
                } else if (tk->type == FLOAT) {
                    val2 = tk->doubleValue;
                }
                double result;
                if (obj->op == PLUS) {
                    result = val1 + val2;
                }
                if (obj->op == MINUS) {
                    result = val1 - val2;
                }
                if (obj->op == MULTIPLY) {
                    result = val1 * val2;
                }
                if (obj->op == DIVIDE) {
                    if (val2 == 0) {
                        result = 0;
                    } else {
                        result = val1 / val2;
                    }
                }

                token* valuee = tk;
                
                token* valueen = obj->value;
                
                if ((obj->value->type == INT) && (tk->type == INT)) {
                    obj->value = Token(INT, NULL, obj->value->pos, obj->value->line);
                    obj->value->intValue = (int)(result);
                } else {
                    obj->value = Token(FLOAT, NULL, obj->value->pos, obj->value->line);
                    obj->value->doubleValue = (result);
                };
                if (obj->op == DIVIDE) {
                    free(obj->value);
                    obj->value = Token(FLOAT, NULL, obj->value->pos, obj->value->line);
                    obj->value->doubleValue = (result);
                }
                freetk(valuee);
                freetk(valueen);
            }
            obj->op = NO_OP;
        } else if ((tk->type == IDENTIFIER) && ((obj->pos+1) < obj->listlen) && (((token*)getItem(obj->tokens, obj->pos+1))->type == ASSIGN)) {
            obj->holder = concat(tk->value, "");
            if (obj->pos != 0) {
                error("SyntaxError", "detected tokens before variable assignment.", tk->line, tk->pos);
            }
            freetk(tk);
            freetk((token*)getItem(obj->tokens, obj->pos+1));
            obj->pos++;
            obj->ins = (char*)createParser(split_tt(obj->tokens, obj->pos+1));
            ((Parser*)obj->ins)->stop = obj->pos;
            obj->tk2 = parse((Parser*)obj->ins);
            ((Parser*)obj->ins)->variables = obj->variables;
            setv(obj->variables, obj->holder, obj->tk2);
            obj->pos = obj->pos + ((Parser*)obj->ins)->pos;
            setItem(obj->tokens, obj->pos, (char*)copytk(obj->tk2));
            obj->pos--;
            free(obj->ins);
            return obj->tk2;
        } else if ((tk->type == IDENTIFIER)) {
            int y = 0;
            int x = listlen(obj->variables);
            printf("\nNEW VARIABLE TABLE (%i variable(s)) : \n", x);

            while (y < x) {
                var* ik = (var*)getItem(obj->variables, y);
                printf("%s: %s\n", ik->name, nam(ik->value->type));
                y++;
            }
            token* val = copytk(getv(obj->variables, tk->value));
            if(val == NULL)
            {
                char* err = "Variable '";
                char* errc = concat(err, tk->value);
                err = concat(errc, "' doesn't exist.");
                free(errc);
                errc = err;
                error("VariableError", errc, tk->line, tk->pos);
                free(errc);
            }
            setItem(obj->tokens, obj->pos, (char*)val);
            obj->pos--;
            freetk(tk);
        } else if ((tk->type >= PLUS) && (tk->type <= DIVIDE)) {
            if (obj->op != NO_OP) {
                char* f = "two signs detected '";
                char* fe = concat(f, nam(obj->op));
                f = fe;
                fe = concat(fe, "' and '");
                free(f);
                f = fe;
                fe = concat(fe, nam(tk->type));
                free(f);
                f = fe;
                fe = concat(fe, "'");
                free(f);
                error("OperationError", fe, tk->line, tk->pos);
                free(fe);
            } else {
                obj->op = tk->type;
                free(tk);
                
            }
        } else if (tk->type == L_PAREN) {
            freetk(tk);
            obj->ins = (char*)createParser(split_tt(obj->tokens, obj->pos+1));
            ((Parser*)obj->ins)->stop = R_PAREN;
            obj->tk2 = parse((Parser*)obj->ins);
            obj->pos = (((Parser*)obj->ins)->pos + obj->pos);
            setItem(obj->tokens, obj->pos, (char*)(((Parser*)(obj->ins))->value));
            obj->pos-=1;

            free(obj->ins);
        } else if (tk->type == STRING) {
            if (obj->op == NO_OP) {
                obj->value = tk;
            } else {
                if (obj->op != PLUS) {
                    char* df = concat("expected plus not ", nam(obj->op));
                    error("StringError", df, tk->line, tk->pos);
                    free(df);
                } else {
                    if (obj->value->type == STRING) {
                        token* tk2 = Token(STRING, concat(obj->value->value, tk->value), tk->pos, tk->line);
                        freetk(tk);
                        freetk(obj->value);
                        obj->value = tk2;
                    } else {
                        char* err = "Cannot do operations on type '";
                        char* errc = concat(err, nam(obj->value->type));
                        err = errc;
                        errc = concat(err, "' with type '");
                        free(err);
                        err = errc;
                        errc = concat(err, nam(tk->type));
                        free(err);
                        err = errc;
                        errc = concat(err, "'");
                        free(err);
                        error("OperationError", errc, tk->line, tk->pos);
                        free(errc);
                    }
                }
            }
            obj->op = NO_OP;
        }
        obj->pos++;
    }
    return obj->value;
}