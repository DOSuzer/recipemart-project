import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from users.api.serializers import UserDetailSerializer

from ..models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredients,
                      RecipeTags, Shoplist, Tag)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class RecipeIngredientsSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        fields = ('id', 'name', 'measurement_unit', 'amount')
        model = RecipeIngredients


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, )
    author = UserDetailSerializer(read_only=True, )
    ingredients = RecipeIngredientsSerializer(source='recipeingredients_set',
                                              many=True, )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        model = Recipe

    def get_is_favorited(self, obj):
        return Favorite.objects.filter(
            user=self.context['request'].user.id, recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        return Shoplist.objects.filter(
            user=self.context['request'].user.id, recipe=obj.id
        ).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = RecipeIngredientsSerializer(source='recipeingredients_set',
                                              many=True, )
    image = Base64ImageField()

    class Meta:
        fields = (
            'ingredients', 'tags',
            'image', 'name', 'text', 'cooking_time'
        )
        model = Recipe

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    def create_ingredients(self, ingredients, instance):
        for ingredient in ingredients:
            current_ingredient = ingredient['ingredient']['id']
            RecipeIngredients.objects.create(ingredient=current_ingredient,
                                             recipe=instance,
                                             amount=ingredient['amount'])

    def create(self, validated_data):
        ingredients = validated_data.pop('recipeingredients_set')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients, recipe)
        for tag in tags:
            RecipeTags.objects.create(tag=tag, recipe=recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipeingredients_set')
        RecipeIngredients.objects.filter(recipe=instance).delete()
        self.create_ingredients(ingredients, instance)
        return super().update(instance, validated_data)


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.CharField(read_only=True,
                                  source='following.email')
    id = serializers.PrimaryKeyRelatedField(read_only=True,
                                            source='following.id')
    username = serializers.CharField(read_only=True,
                                     source='following.username')
    first_name = serializers.CharField(read_only=True,
                                       source='following.first_name')
    last_name = serializers.CharField(read_only=True,
                                      source='following.last_name')
    is_subscribed = serializers.BooleanField(default=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        try:
            recipes_limit = (self.context['request'].
                             query_params.get('recipes_limit'))
            recipes = obj.following.recipes.all()[:int(recipes_limit)]
        except KeyError:
            recipes = obj.following.recipes.all()
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(
            author=obj.following.id
        ).count()

    class Meta:
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        model = Follow
