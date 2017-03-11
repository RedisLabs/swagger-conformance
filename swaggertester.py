import logging

from pyswagger import App, Security
from pyswagger.contrib.client.requests import Client
# pyswagger makes INFO level logs regularly by default, so lower its logging
# level to prevent the spam.
logging.getLogger("pyswagger").setLevel(logging.WARNING)


log = logging.getLogger(__name__)


class SwaggerClient:
    """Client to use to access the Swagger application."""

    def __init__(self, schema_path):
        self._app = App.create(schema_path)

    @property
    def app(self):
        return self._app

    def request(self, operation, parameters):
        """Perform a request.

        :param operation: The operation to perform.
        :type operation: OperationTemplate
        :param parameters: The parameters to use on the operation.
        :type parameters: dict
        """
        client = Client(Security(self._app))
        result = client.request(operation.operation(**parameters))

        return result


class ParameterTemplate:
    """Template for a parameter to pass to an operation on an endpoint."""

    def __init__(self, parameter):
        assert parameter.type is not None
        self._type = parameter.type
        assert parameter.name is not None
        self._name = parameter.name

    def __repr__(self):
        return "{}(name={}, type={})".format(self.__class__.__name__,
                                             self._name,
                                             self._type)

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type


class OperationTemplate:
    """Template for an operation on an endpoint."""

    def __init__(self, app, operation):
        self._app = app
        self._operation = operation
        self._parameters = {}

        self._populate_parameters()

    def __repr__(self):
        return "{}(name={}, type={})".format(self.__class__.__name__,
                                             self._operation,
                                             self._parameters)

    @property
    def operation(self):
        return self._operation

    @property
    def parameters(self):
        return self._parameters

    def _populate_parameters(self):
        for parameter in self._operation.parameters:
            log.debug("Handling parameter: %r", parameter.name)

            if parameter.schema is None:
                log.debug("Fully defined parameter")
                param_template = ParameterTemplate(parameter)
                self._parameters[parameter.name] = param_template
            else:
                log.debug("Schema defined parameter")
                log.warning("SKIPPING SCHEMA PARAM - NOT IMPLEMENTED")


class EndpointCollection:

    operations = ["get", "put"]

    def __init__(self, client):
        log.debug("Creating new endpoint collection for: %r", client)
        self._client = client
        self._app = client.app

        self._paths = self._app.root.paths.keys()
        log.debug("Found paths as: %s", self._paths)

        self._expanded_paths = {}
        for path in self._paths:
            self._expanded_paths[path] = self._expand_path(path)

    @property
    def endpoints(self):
        return self._expanded_paths

    def _expand_path(self, path):
        log.debug("Expanding path: %r", path)

        operations_map = {}
        for operation_name in self.operations:
            log.debug("Accessing operation: %s", operation_name)
            operation = getattr(self._app.root.paths[path], operation_name)
            if operation is not None:
                log.debug("Have operation")
                operations_map[operation_name] = OperationTemplate(self._app,
                                                                   operation)

        log.debug("Expanded path as: %r", operations_map)
        return operations_map


def main(schema_path):
    client = SwaggerClient(schema_path)
    endpoints = EndpointCollection(client)
    log.debug("Expanded endpoints as: %r", endpoints)

    operation = endpoints.endpoints['/apps/{appid}']['get']
    print(operation)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main('http://127.0.0.1:5000/api/schema')
