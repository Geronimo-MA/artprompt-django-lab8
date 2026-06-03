from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from .models import ArtPrompt, Category, TagPrompt, PromptMeta


class HasTagsFilter(admin.SimpleListFilter):
    title = 'Наличие тегов'
    parameter_name = 'has_tags'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'С тегами'),
            ('no', 'Без тегов'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(tags__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(tags__isnull=True)
        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(TagPrompt)
class TagPromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag', 'slug')
    list_display_links = ('id', 'tag')
    search_fields = ('tag',)
    prepopulated_fields = {'slug': ('tag',)}
    ordering = ('tag',)


from django.contrib import admin
from .models import PromptMeta

@admin.register(PromptMeta)
class PromptMetaAdmin(admin.ModelAdmin):
    # Список полей для отображения
    list_display = ('id', 'style', 'estimated_time')
    ordering = ['style']


@admin.register(ArtPrompt)
class ArtPromptAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'post_photo',
        'style',
        'status',
        'cat',
        'short_content',
        'tags_count',
        'time_create',
    )

    list_display_links = ('title',)
    list_editable = ('status',)
    ordering = ('-time_create', 'title')
    list_per_page = 10

    search_fields = ('title', 'content', 'style', 'cat__name', 'tags__tag')

    list_filter = (
        'status',
        'cat',
        'tags',
        HasTagsFilter,
        'time_create',
    )

    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)

    fields = (
        'title',
        'slug',
        'content',
        'photo',
        'style',
        'status',
        'cat',
        'tags',
        'meta',
        'time_create',
        'time_update',
    )

    readonly_fields = ('time_create', 'time_update')

    actions = ('set_published', 'set_draft')

    @admin.display(description='Краткое описание')
    def short_content(self, obj):
        if not obj.content:
            return 'Описание отсутствует'

        if len(obj.content) > 60:
            return f'{obj.content[:60]}...'

        return obj.content

    @admin.display(description='Количество тегов')
    def tags_count(self, obj):
        return obj.tags.count()

    @admin.display(description='Изображение')
    def post_photo(self, obj):
        if obj.photo:
            return mark_safe(f"<img src='{obj.photo.url}' width='60'>")
        return 'Без изображения'

    @admin.action(description='Опубликовать выбранные арт-промпты')
    def set_published(self, request, queryset):
        count = queryset.update(status=ArtPrompt.Status.PUBLISHED)
        self.message_user(
            request,
            f'Опубликовано {count} арт-промптов.',
            messages.SUCCESS
        )

    @admin.action(description='Снять выбранные арт-промпты с публикации')
    def set_draft(self, request, queryset):
        count = queryset.update(status=ArtPrompt.Status.DRAFT)
        self.message_user(
            request,
            f'{count} арт-промптов снято с публикации.',
            messages.WARNING
        )