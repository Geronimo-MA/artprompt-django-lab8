from django.db import models
from django.urls import reverse


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=ArtPrompt.Status.PUBLISHED)


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='Название категории'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Slug'
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('category', kwargs={'cat_slug': self.slug})

    def __str__(self):
        return self.name


class TagPrompt(models.Model):
    tag = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='Тег'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Slug'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['tag']

    def get_absolute_url(self):
        return reverse('tag', kwargs={'tag_slug': self.slug})

    def __str__(self):
        return self.tag


class PromptMeta(models.Model):
    style = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Стиль'
    )
    estimated_time = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Примерное время выполнения, мин.'
    )

    class Meta:
        verbose_name = 'Дополнительная информация'
        verbose_name_plural = 'Дополнительная информация'

    def __str__(self):
        if self.style and self.estimated_time:
            return f'{self.style}, {self.estimated_time} мин.'
        if self.style:
            return self.style
        if self.estimated_time:
            return f'{self.estimated_time} мин.'
        return 'Дополнительная информация'


class ArtPrompt(models.Model):
    class Status(models.IntegerChoices):
        DRAFT = 0, 'Черновик'
        PUBLISHED = 1, 'Опубликовано'

    title = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Slug'
    )
    content = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    photo = models.ImageField(
        upload_to='photos/%Y/%m/%d/',
        default=None,
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    style = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Стиль'
    )
    status = models.IntegerField(
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Статус'
    )
    time_create = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания'
    )
    time_update = models.DateTimeField(
        auto_now=True,
        verbose_name='Время изменения'
    )

    cat = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='prompts',
        verbose_name='Категория'
    )

    tags = models.ManyToManyField(
        TagPrompt,
        blank=True,
        related_name='prompts',
        verbose_name='Теги'
    )

    meta = models.OneToOneField(
        PromptMeta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prompt',
        verbose_name='Дополнительная информация'
    )

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        verbose_name = 'Арт-промпт'
        verbose_name_plural = 'Арт-промпты'
        ordering = ['-time_create']
        permissions = [
            ('can_publish_prompt', 'Может публиковать арт-промпты'),
        ]

    def get_absolute_url(self):
        return reverse('idea_slug', kwargs={'idea_slug': self.slug})

    def __str__(self):
        return self.title


class UploadedFile(models.Model):
    file = models.FileField(
        upload_to='uploads_model/%Y/%m/%d/',
        verbose_name='Файл'
    )
    time_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время загрузки'
    )

    def __str__(self):
        return self.file.name

    class Meta:
        verbose_name = 'Загруженный файл'
        verbose_name_plural = 'Загруженные файлы'