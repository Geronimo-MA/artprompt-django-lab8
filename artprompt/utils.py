# artprompt/utils.py
from .models import Category, TagPrompt

class DataMixin:
    paginate_by = 3

    def get_mixin_context(self, context: dict, **kwargs) -> dict:
        context['db_categories'] = Category.objects.all()
        context['tags'] = TagPrompt.objects.all()
        context.setdefault('cat_selected', None)
        context.setdefault('selected_tag', None)
        context.update(kwargs)
        return context