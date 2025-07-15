# flake8: noqa: D106
"""Сериализаторы Пользователя."""
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers

from users.models import CustomUser
from recipes.models import Ingredient, Tag, Recipe, RecipeIngredient


class UsersSerializer(UserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.BooleanField(default=False, read_only=True)
    avatar = Base64ImageField()

    class Meta():
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar',
        )


class CustomUsersCreateSerializer(UserCreateSerializer):
    """Кастомный Сериализатор унаследованный от djoser."""

    password = serializers.CharField(write_only=True)

    class Meta():
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password',)


class CustomAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)

class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

class RecipeGet(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UsersSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.BooleanField(default=False, read_only=True) # ТРЕБУЕТ ДОРОБОТКИ!
    is_in_shopping_cart = serializers.BooleanField(default=False, read_only=True) # ТРЕБУЕТ ДОРОБОТКИ!
    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',)



class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    author = UsersSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time', 'author')

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
    
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(Ingredient, pk=ingredient_data['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount'])
        return recipe
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('recipe_ingredients', None)

        if tags is not None:
            instance.tags.set(tags)
        
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()

            for ingredient_data in ingredients_data:
                ingredient = get_object_or_404(Ingredient, pk=ingredient_data['id'])
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                ) 
        return instance
    
    def to_representation(self, instance):
        return RecipeGet(instance, context={
            'request': self.context.get('request')
        }).data