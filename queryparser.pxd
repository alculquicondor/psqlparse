cdef extern from "queryparser.h":
    int do_parse(const char* query, char** output)
