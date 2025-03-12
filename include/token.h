#ifndef TOKEN_LIB
#define TOKEN_LIB
#endif

enum token_type {
    INT,
    STRING,
    PLUS, // DO NOT CHARGE ORDER FROM HERE
    MINUS, // ...
    MULTIPLY, // ...
    DIVIDE, // TO HERE
    FLOAT,
    L_PAREN,
    R_PAREN,
    L_BRACKET, // []
    R_BRACKET,
    L_BRACE,
    R_BRACE,
    IDENTIFIER,
    EQUAL,
    ASSIGN,
    GREATER,
    LESSER,
    GREATER_EQUAL,
    LESSER_EQUAL,
    NOT_EQUAL,
    COLON,
    SEMICOLON,
    NO_OP
};



typedef struct token {
    int type;
    char* value;
    double doubleValue;
    int intValue;
    int pos;
    int line;
    int ref;
} token;

typedef struct list {
    char* next;
    char* value;

} list;

typedef struct var {
    char* name;
    token* value;
} var;

token* getv(list* vr, char* name);
var* setv(list* vr, char* name, token* value);
char* getItem(list* lst, int item);
char* setItem(list* lst, int item, char* value);
char* addItem(list* lst, char* value);
list* createList();
list* PopItem(list* lst);
token* Token(int id, char* value, int pos, int line);
int listlen(list* lst);
int error(char* errtype, char* context, int line, int pos);
list* split_tt(list* lst, int item);
token* copytk(token* tk);
int cmps(char* a, char* b);