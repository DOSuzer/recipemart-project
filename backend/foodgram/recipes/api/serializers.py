from rest_framework import serializers

from core.fields import Base64ImageField
from users.api.serializers import UserDetailSerializer
from ..models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                      RecipeTag, Shoplist, Tag)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class RecipeIngredientSerializer(serializers.HyperlinkedModelSerializer):
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
        model = RecipeIngredient


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, )
    author = UserDetailSerializer(read_only=True, )
    ingredients = RecipeIngredientSerializer(source='RecipeIngredients_set',
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
    ingredients = RecipeIngredientSerializer(source='RecipeIngredient_set',
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
        objs = [
            RecipeIngredient(
                ingredient=ingredient['ingredient']['id'],
                recipe=instance,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(objs)

    def create(self, validated_data):
        ingredients = validated_data.pop('RecipeIngredient_set')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients, recipe)
        for tag in tags:
            RecipeTag.objects.create(tag=tag, recipe=recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('RecipeIngredient_set')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def validate(self, data):
        ingredients = data.get('RecipeIngredient_set')
        temp_list = []
        for ingredient in ingredients:
            if ingredient['ingredient']['id'] in temp_list:
                raise serializers.ValidationError(
                    'Обнаружен дубликат ингредиента: {}!'
                    .format(ingredient['ingredient']['id'])
                )
            temp_list.append(ingredient['ingredient']['id'])
        return data


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
