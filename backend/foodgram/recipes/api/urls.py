from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FavoriteViewSet, IngredientViewSet, RecipesViewSet,
                    ShoppingListViewSet, SubscribeView, SubscriptionsView,
                    TagViewSet)

router = DefaultRouter()
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('recipes', ShoppingListViewSet, basename='shopping_list')
router.register('recipes', FavoriteViewSet, basename='favorite')
router.register('users/subscriptions', SubscriptionsView,
                basename='subscriptions')
router.register(r'users/(?P<user_id>[\d]+)/subscribe', SubscribeView,
                basename='subscribe')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
]
