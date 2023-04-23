from core.permissions import IsAuthorOrReadOnly
from core.renderers import ShoppingListTextDataRenderer
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from ..models import Favorite, Follow, Ingredient, Recipe, Shoplist, Tag, User
from .serializers import (FollowSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          ShortRecipeSerializer, TagSerializer)


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (permissions.AllowAny, )


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny, )

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name is not None:
            queryset = queryset.filter(name=name)
        return queryset


class RecipesViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = PageNumberPagination
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FavoriteViewSet(mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):

    @action(detail=False,
            methods=['post', 'delete'],
            url_path=r'(?P<recipe_id>[\d]+)/favorite')
    def add_delete_favorite(self, request, recipe_id):
        user = get_object_or_404(User, pk=self.request.user.id)
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if self.request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Уже добавлено в избранное"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(data=serializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            Favorite.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsView(mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    pagination_class = PageNumberPagination
    serializer_class = FollowSerializer

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.request.user.id)
        queryset = user.follower.all()
        recipes_limit = self.request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            queryset = queryset[0:recipes_limit]
        return queryset


class SubscribeView(mixins.CreateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = FollowSerializer

    def create(self, request, user_id):
        user = get_object_or_404(User, pk=self.request.user.id)
        following = get_object_or_404(User, pk=user_id)
        if user == following:
                return Response(
                    {"errors": "Нельзя подписаться на себя!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if Follow.objects.filter(user=user, following=following).exists():
                return Response(
                    {"errors": "Уже подписан, угомонись!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        serializer = FollowSerializer(Follow.objects.create(
                                      user=user, following=following))
        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=self.request.user.id)
        following = get_object_or_404(User, pk=kwargs.get('user_id'))
        Follow.objects.filter(user=user, following=following).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingListViewSet(mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        renderer_classes=[ShoppingListTextDataRenderer],
    )
    def download_shopping_list(self, request):
        user = get_object_or_404(User, pk=self.request.user.id)
        file_name = f'shopping_list.{request.accepted_renderer.format}'
        shopping_list = (
            Shoplist.objects
            .filter(user=user.id)
            .prefetch_related('recipe')
            .values(
                name=F('recipe__ingredients__name'),
                unit=F(
                    'recipe__recipeingredients__ingredient__measurement_unit'
                )
            )
            .annotate(amount=Sum('recipe__recipeingredients__amount'))
            .order_by('recipe__ingredients__name')
        )
        return Response(
            shopping_list,
            headers=(
                {"Content-Disposition": f'attachment; filename="{file_name}"'}
            )
        )

    @action(detail=False,
            methods=['post', 'delete'],
            url_path=r'(?P<recipe_id>[\d]+)/shopping_cart')
    def add_remove_shopping_list(self, request, recipe_id):
        user = get_object_or_404(User, pk=self.request.user.id)
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if self.request.method == 'POST':
            if Shoplist.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Уже добавлено в список покупок"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Shoplist.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(data=serializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            Shoplist.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
