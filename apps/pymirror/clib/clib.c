#define PY_SSIZE_T_CLEAN  // Add this line BEFORE #include <Python.h>
#include <Python.h>
#include <stdlib.h>
#include <string.h>

static PyObject* rgba_to_rgb16(PyObject* self, PyObject* args) {
    const char* rgba;
    Py_ssize_t data_len;
    int width, height;
    
    if (!PyArg_ParseTuple(args, "y#ii", &rgba, &data_len, &width, &height)) {
        return NULL;
    }
    // Convert RGBA to RGB565
    int rgb565_size = width * height * sizeof(unsigned short);
    unsigned short *rgb565 = malloc(rgb565_size);
    if (!rgb565) return NULL;

    for (int i = 0; i < width * height; ++i)
    {
        unsigned char r = rgba[i * 4];
        unsigned char g = rgba[i * 4 + 1];
        unsigned char b = rgba[i * 4 + 2];

        // Convert to RGB565 format
        rgb565[i] = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
    }
    PyObject *result = PyBytes_FromStringAndSize((char*)rgb565, rgb565_size);
    free(rgb565); // Free the C buffer after creating the Python object
    return result;
}

static PyObject* rgb_to_rgb16(PyObject* self, PyObject* args) {
    const char* rgb;
    Py_ssize_t data_len;
    int width, height;

    if (!PyArg_ParseTuple(args, "y#ii", &rgb, &data_len, &width, &height)) {
        return NULL;
    }
    // Convert RGB to RGB565
    int rgb565_size = width * height * sizeof(unsigned short);
    unsigned short *rgb565 = malloc(rgb565_size);
    if (!rgb565) return NULL;

    for (int i = 0; i < width * height; ++i)
    {
        unsigned char r = rgb[i * 3];
        unsigned char g = rgb[i * 3 + 1];
        unsigned char b = rgb[i * 3 + 2];

        // Convert to RGB565 format
        rgb565[i] = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
    }
    PyObject *result = PyBytes_FromStringAndSize((char*)rgb565, rgb565_size);
    free(rgb565);  // Free the C buffer after creating the Python object
    return result;
}

static PyMethodDef clib_methods[] = {
    {"rgba_to_rgb16", rgba_to_rgb16, METH_VARARGS, "Convert RGBA to RGB565"},
    {"rgb_to_rgb16", rgb_to_rgb16, METH_VARARGS, "Convert RGB to RGB565"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef clib_module = {
    PyModuleDef_HEAD_INIT,
    "clib",
    "C library for image conversion",
    -1,
    clib_methods
};

// This is the required function name for Python 3
PyMODINIT_FUNC PyInit_clib(void) {
    return PyModule_Create(&clib_module);
}