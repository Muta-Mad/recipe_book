from django_filters import CharFilter, FilterSet, NumberFilter, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Фильтр ингредиентов."""
    name = CharFilter(field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Фильтр рецептов."""
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )
    author = NumberFilter(field_name='author__id')
    is_favorited = NumberFilter(method='filter_favorite')
    is_in_shopping_cart = NumberFilter(method='filter_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author',)

    def filter_favorite(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favor_recipe__user=self.request.user)
        return queryset

    def filter_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shpg_recipe__user=self.request.user)
        return queryset
