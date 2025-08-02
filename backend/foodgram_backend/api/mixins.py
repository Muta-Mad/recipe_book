from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


class ListRetrieveViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    """ViewSet только для списка объектов и детального просмотра."""
    pass


class CreateDestroyViewSet(
    mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericViewSet
):
    """ViewSet только для создания и удаления объектов."""
    pass
