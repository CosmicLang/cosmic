LEXER_LIB = include/lexer.c
TOKEN_LIB = include/token.c
PARSER_LIB = include/parser.c

MAIN = main.c
OUTPUT_FILE = main

build:
	gcc -Iinclude $(TOKEN_LIB) $(PARSER_LIB) $(LEXER_LIB) $(MAIN) -o $(OUTPUT_FILE)
	./$(OUTPUT_FILE)