import io

from django.db.models import F, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.filters import IngredientsSearchFilter, RecipeFilter
from core.pagination import CustomPagination
from core.permissions import IsAuthorOrReadOnly
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


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny, )
    filter_backends = [IngredientsSearchFilter, ]
    search_fields = ('^name', )
    queryset = Ingredient.objects.all()
    http_method_names = ['get', ]


class RecipesViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    filter_backends = [rest_framework.DjangoFilterBackend, ]
    filter_fields = ('author', )

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_remove_class_object(self, class_name, request, pk):
        user = get_object_or_404(User, pk=request.user.id)
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if class_name.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Уже добавлено в список покупок"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            class_name.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(data=serializer.data,
                            status=status.HTTP_201_CREATED)
        class_name.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            url_path=r'shopping_cart')
    def add_remove_shopping_list(self, request, pk):
        return self.add_remove_class_object(Shoplist, request, pk)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
    )
    def download_shopping_list(self, request):
        user = get_object_or_404(User, pk=self.request.user.id)
        shopping_list = (
            Shoplist.objects
            .filter(user=user.id)
            .prefetch_related('recipe')
            .values(
                name=F('recipe__ingredients__name'),
                unit=F(
                    'recipe__recipeingredient__ingredient__measurement_unit'
                )
            )
            .annotate(amount=Sum('recipe__recipeingredient__amount'))
            .order_by('recipe__ingredients__name')
        )
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('FreeSans', 'FreeSans.ttf'))
        p.setFont('FreeSans', 12)
        p.drawString(100, 750, '                              СПИСОК ПОКУПОК:')
        p.drawString(100, 730, 'Название:')
        p.drawString(400, 730, 'Кол-во:')
        p.drawString(500, 730, 'Ед. изм.:')
        y = 700
        for item in shopping_list:
            p.drawString(100, y, item['name'])
            p.drawString(400, y, str(item['amount']))
            p.drawString(500, y, item['unit'])
            y -= 20
            if y < 100:
                p.showPage()
                p.setFont('FreeSans', 12)
                y = 700
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename="shopping_list.pdf")

    @action(detail=True,
            methods=['post', 'delete'],
            url_path=r'favorite')
    def add_delete_favorite(self, request, pk):
        return self.add_remove_class_object(Favorite, request, pk)


class SubscriptionsView(mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    pagination_class = CustomPagination
    serializer_class = FollowSerializer

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.request.user.id)
        return user.follower.all()


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
