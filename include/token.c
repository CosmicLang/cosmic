#include <token.h>

#ifndef NULL
#define NULL (void*)(0)
#endif
#ifndef STDHD_IMP
#define STDHD_IMP
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#endif



char* getItem(list* lst, int item) {
    while (item != 0) {
        if (lst->next != (char*)(0)) {
            lst = (list*)lst->next;
        };
        item--;
    }
    return lst->value;
}

char* setItem(list* lst, int item, char* value) {
    while (item != 0) {
        if (lst->next != NULL) {
            lst = (list*)lst->next;
        };
        item--;
    }
    if (lst != NULL) {
        lst->value = value;
    }
    return value;
}

char* addItem(list* lst, char* value) {
    if(lst->value == NULL) {
        lst->value = value;
        return value;
    }
    while(lst->next != NULL) {
        lst = (list*)lst->next;
    };
    list* nlst = malloc(sizeof(list));
    nlst->next = NULL;
    nlst->value = value;
    lst->next = (char*)nlst;
    return value;
}

list* createList() {
    list* nlst = malloc(sizeof(list));
    nlst->value = NULL;
    nlst->next = NULL;
    return nlst;
}

list* PopItem(list* lst) {
    list* prev_node = NULL;
    list* nlst = lst;
    if (lst->value = NULL) {
        return nlst;
    }
    while (lst->next != NULL) {
        prev_node = lst;
        lst = (list*)lst->next;
    }
    if (prev_node != NULL) {
        prev_node->next=NULL;
    }
    free(lst);
    return nlst;
}

int listlen(list* lst) {
    int l = 0;
    if (lst->value != NULL) {
        l++;
        while (lst->next != NULL) {
            lst = (list*)(lst->next);
            l++;
        };
    }
    return l;
}

token* Token(int id, char* value, int pos, int line) {
    token* tk = malloc(sizeof(token));
    tk->type = id;
    tk->value = value;
    tk->pos = pos;
    tk->line = line;
    double doubleValue = 0;
    int intValue = 0;
    float floatValue = 0.0;
    tk->ref=1;
    return tk;
};

int error(char* errtype, char* context, int line, int pos) {
    printf("%s: %s at line %i, position %i.\n", errtype, context, line, pos);
    exit(1);
}
list* split_tt(list* lst, int item) {
    while (item != 0) {
        if (lst->next != (char*)(0)) {
            lst = (list*)lst->next;
        };
        item--;
    }
    return lst;
};

void freeList(list* lst) {
    free(lst);
    if (!(lst->value == NULL)) {
        while (lst->next != NULL) {
            lst = (list*)(lst->next);
            free(lst);
        }
    }
}

int cmps(char* a, char* b) {
    if (strlen(a) != strlen(b)) {
        return 1;
    } else{
        int i = 0;
        int l = strlen(a);
        while (i < l) {
            if ((a[i] != b[i])) {
                return 1;
            }
            i++;
        }
    }
    return 0;
}

token* getv(list* vr, char* name) {
    int lslen = listlen(vr);
    int pos = 0;
    while (pos < lslen) {
        var* v = (var*)getItem(vr, pos);
        if (cmps(name, v->name) == 0) {
            return v->value;
        }
        pos++;
    }
    return NULL;
}
var* setv(list* vr, char* name, token* value) {
    int lslen = listlen(vr);
    int pos = 0;
    while (pos < lslen) {
        var* v = (var*)getItem(vr, pos);
        if (cmps(name, v->name) == 0) {
            v->value = value;
            return v;
        }
        pos++;
    }
    var* v = malloc(sizeof(var));
    v->name = name;
    v->value = value;
    addItem(vr, (char*)v);
    return v;
}

token* copytk(token* tk) {
    token* tk2 = malloc(sizeof(token));
    tk2->doubleValue = tk->doubleValue;
    tk2->intValue = tk->intValue;
    tk2->value = tk->value;
    tk2->pos = tk->pos;
    tk2->line = tk->line;
    tk2->ref = 1;
    tk2->type = tk->type;
    return tk2;
}