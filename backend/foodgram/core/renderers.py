import io

from rest_framework import renderers

SHOPPING_LIST_FILE_HEADERS = ['name', 'unit', 'amount']


class ShoppingListTextDataRenderer(renderers.BaseRenderer):

    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):

        text_buffer = io.StringIO()
        text_buffer.write(
            ' '.join(header for header in SHOPPING_LIST_FILE_HEADERS) + '\n'
        )

        for recipe_data in data:
            text_buffer.write(
                ' '.join(str(rd) for rd in list(recipe_data.values())) + '\n'
            )

        return text_buffer.getvalue()
