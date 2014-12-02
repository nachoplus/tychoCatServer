 %module ucac4
 %{
 /* Includes the header in the wrapper code */
 #include "ucac4.h"
 %}
 
 /* Parse the header file to generate wrappers */
 %include "ucac4.h"
FILE *fopen(const char *filename, const char *mode);
int fclose(FILE * filename);


/* 
 * Type mapping for grabbing a FILE * from Python
 * Taken from the Swig documentation ... 

%include "ucac4.h"
%typemap(python,in) FILE * {
  if (!PyFile_Check($input)) {
      PyErr_SetString(PyExc_TypeError, "Need a file!");
      goto fail;
  }
  $1 = PyFile_AsFile($input);
}
 */
