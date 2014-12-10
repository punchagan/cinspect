#include <Python.h>

// start: say_hello
static PyObject*
say_hello(PyObject* self, PyObject* args)
{
    const char* name;

    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    printf("Hello %s!\n", name);

    Py_RETURN_NONE;
}
// end: say_hello

static PyMethodDef HelloMethods[] =
{
     {"say_hello", say_hello, METH_VARARGS, "Greet somebody."},
     {NULL, NULL, 0, NULL}
};


#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC PyInit_hello(void){
  static struct PyModuleDef moduledef = {PyModuleDef_HEAD_INIT, "hello", "Docs", -1, HelloMethods};
  return PyModule_Create(&moduledef);
}
#else
PyMODINIT_FUNC inithello(void)
{
  (void) Py_InitModule("hello", HelloMethods);
}
#endif
