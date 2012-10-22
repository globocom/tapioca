from tapioca import ResourceHandler


class ResourceWithDocumentation(ResourceHandler):
    """
    This is my resource
    """

    def create_model(self, model):
        """
        Creates a new instance of the resource
        """
        return {}

    def get_collection(self, callback):
        """
        Gets all instances of the resource
        """
        callback([])

    def get_model(self, cid, *args):
        """
        Gets an instance of the resource
        """
        return {}

    def update_model(self, model, cid, *args):
        """
        Update a specific instance of the resource
        """
        pass

    def delete_model(self, cid):
        """
        Deletes an intance of the resource
        """
        pass


