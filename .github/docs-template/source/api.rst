
Protoplaster Server API Reference
---------------------------------

Error Handling
~~~~~~~~~~~~~~

Should an error occur during the handling of an API request, either because of incorrect request data or other endpoint-specific scenarios, the server will return an error structure containing a user-friendly description of the error.
An example error response is shown below:

.. sourcecode:: json

   {
      "error": "test start failed"
   }


Configs API
~~~~~~~~~~~

.. autoflask:: protoplaster.protoplaster:create_docs_app()
   :modules: protoplaster.api.v1.configs
   :undoc-static:
   :order: path

Test Runs API
~~~~~~~~~~~~~

.. autoflask:: protoplaster.protoplaster:create_docs_app()
   :modules: protoplaster.api.v1.test_runs
   :undoc-static:
   :order: path
