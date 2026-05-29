from __future__ import annotations

from typing import Type

from django.db.models import Model
from rest_framework import serializers as drf_serializers


def add_to_user_list(model_class: Type[Model], user_id: int, recipe_id: int) -> None:
    """Добавляет рецепт в список пользователя (избранное/корзина).

    Raises ValidationError если рецепт уже в списке.
    """
    if model_class.objects.filter(user_id=user_id, recipe_id=recipe_id).exists():
        raise drf_serializers.ValidationError(
            {'detail': 'Рецепт уже в списке.'}
        )
    model_class.objects.create(user_id=user_id, recipe_id=recipe_id)


def remove_from_user_list(
    model_class: Type[Model], user_id: int, recipe_id: int
) -> bool:
    """Удаляет рецепт из списка пользователя. Возвращает True если удалено."""
    count, _ = model_class.objects.filter(
        user_id=user_id, recipe_id=recipe_id
    ).delete()
    return bool(count)
