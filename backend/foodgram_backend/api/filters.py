from django_filters import FilterSet, CharFilter, NumberFilter
from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = NumberFilter(field_name='tags__id')
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
