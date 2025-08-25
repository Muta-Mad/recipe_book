from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


class CreateDestroyViewSet(
    mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericViewSet
):
    """ViewSet только для создания и удаления объектов."""
    pass
