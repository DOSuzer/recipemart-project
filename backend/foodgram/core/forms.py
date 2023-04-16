from django import forms
from recipes.models import Favorite, Recipe


class RecipeForm(forms.ModelForm):

    favorite_count = forms.IntegerField(label='Добавлений в избранное')

    def save(self, commit=True):
        id = self.cleaned_data.get('pk', None)
        favorite_count = Favorite.filter(recipe=id).count()
        return super(RecipeForm, self).save(commit=commit)

    class Meta:
        fields = '__all__'
        model = Recipe
