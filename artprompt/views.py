import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F, Value, Count, Sum, Avg, Max, Min
from django.db.models.functions import Length, Concat
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import AddPromptPlainForm, AddPromptModelForm, UploadFileForm
from .models import ArtPrompt, Category, TagPrompt
from .utils import DataMixin


def get_base_context():
    return {
        'db_categories': Category.objects.all(),
        'tags': TagPrompt.objects.all(),
    }


# Главная страница через класс ListView
class ArtPromptHome(LoginRequiredMixin, DataMixin, ListView):
    login_url = 'users:login'
    model = ArtPrompt
    template_name = 'artprompt/index.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return (
            ArtPrompt.published
            .select_related('cat', 'meta')
            .prefetch_related('tags')
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        return self.get_mixin_context(
            context,
            title='ArtPrompt — сайт для художников',
            description='Главная страница проекта с арт-промптами из базы данных.',
            cat_selected=0,
            selected_tag=0,
        )


# Детальная страница арт-промпта через DetailView
class ShowPrompt(LoginRequiredMixin, DataMixin, DetailView):
    login_url = 'users:login'
    model = ArtPrompt
    template_name = 'artprompt/idea_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'idea_slug'

    def get_queryset(self):
        return (
            ArtPrompt.published
            .select_related('cat', 'meta')
            .prefetch_related('tags')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return self.get_mixin_context(
            context,
            title=f'Арт-промпт: {self.object.title}',
            description='Подробная информация о выбранном арт-промпте',
            cat_selected=self.object.cat.id if self.object.cat else None,
            selected_tag=None,
        )


# Добавление арт-промпта через CreateView
class CreatePrompt(LoginRequiredMixin, DataMixin, CreateView):
    login_url = 'users:login'
    form_class = AddPromptModelForm
    template_name = 'artprompt/add_form.html'
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return self.get_mixin_context(
            context,
            title='Добавление арт-промпта через CreateView',
            cat_selected=None,
            selected_tag=None,
        )


# Редактирование арт-промпта через UpdateView
class UpdatePrompt(LoginRequiredMixin, DataMixin, UpdateView):
    login_url = 'users:login'
    model = ArtPrompt
    form_class = AddPromptModelForm
    template_name = 'artprompt/add_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'idea_slug'
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return self.get_mixin_context(
            context,
            title=f'Редактирование арт-промпта: {self.object.title}',
            cat_selected=self.object.cat.id if self.object.cat else None,
            selected_tag=None,
        )


# Удаление арт-промпта через DeleteView
class DeletePrompt(LoginRequiredMixin, DataMixin, DeleteView):
    login_url = 'users:login'
    model = ArtPrompt
    template_name = 'artprompt/prompt_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'idea_slug'
    context_object_name = 'post'
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return self.get_mixin_context(
            context,
            title=f'Удаление арт-промпта: {self.object.title}',
            cat_selected=self.object.cat.id if self.object.cat else None,
            selected_tag=None,
        )


# Страница категории через ListView
class ArtPromptCategory(LoginRequiredMixin, DataMixin, ListView):
    login_url = 'users:login'
    model = ArtPrompt
    template_name = 'artprompt/index.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        self.category = Category.objects.get(slug=self.kwargs['cat_slug'])

        return (
            ArtPrompt.published
            .filter(cat=self.category)
            .select_related('cat', 'meta')
            .prefetch_related('tags')
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        return self.get_mixin_context(
            context,
            title=f'Категория: {self.category.name}',
            description='Арт-промпты выбранной категории.',
            cat_selected=self.category.id,
            selected_tag=0,
        )


# Страница тега через ListView
class ArtPromptTag(LoginRequiredMixin, DataMixin, ListView):
    login_url = 'users:login'
    model = ArtPrompt
    template_name = 'artprompt/index.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        self.tag = TagPrompt.objects.get(slug=self.kwargs['tag_slug'])

        return (
            self.tag.prompts
            .filter(status=ArtPrompt.Status.PUBLISHED)
            .select_related('cat', 'meta')
            .prefetch_related('tags')
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        return self.get_mixin_context(
            context,
            title=f'Тег: {self.tag.tag}',
            description='Арт-промпты с выбранным тегом.',
            cat_selected=None,
            selected_tag=self.tag.id,
        )


# Старый вариант главной страницы через функцию
@login_required
def index(request):
    posts = (
        ArtPrompt.published
        .select_related('cat', 'meta')
        .prefetch_related('tags')
    )

    data = {
        'title': 'ArtPrompt — сайт для художников',
        'description': 'Главная страница проекта с арт-промптами из базы данных.',
        'posts': posts,
        'cat_selected': 0,
        'selected_tag': 0,
        **get_base_context(),
    }

    return render(request, 'artprompt/index.html', data)


@login_required
def about(request):
    data = {
        'title': 'О сайте ArtPrompt',
        'content': (
            'ArtPrompt — учебный Django-проект для художников. '
            'На сайте демонстрируется работа шаблонов, маршрутов, '
            'базы данных, связей между таблицами и ORM-запросов.'
        ),
        'cat_selected': None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/about.html', data)


@login_required
def categories(request):
    data = {
        'title': 'Категории идей',
        'categories': Category.objects.all(),
        'cat_selected': None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/categories.html', data)


@login_required
def show_category(request, cat_slug):
    category = get_object_or_404(Category, slug=cat_slug)

    posts = (
        ArtPrompt.published
        .filter(cat=category)
        .select_related('cat', 'meta')
        .prefetch_related('tags')
    )

    data = {
        'title': f'Категория: {category.name}',
        'description': 'Арт-промпты выбранной категории.',
        'posts': posts,
        'cat_selected': category.id,
        'selected_tag': 0,
        **get_base_context(),
    }

    return render(request, 'artprompt/index.html', data)


@login_required
def show_tag(request, tag_slug):
    tag = get_object_or_404(TagPrompt, slug=tag_slug)

    posts = (
        tag.prompts
        .filter(status=ArtPrompt.Status.PUBLISHED)
        .select_related('cat', 'meta')
        .prefetch_related('tags')
    )

    data = {
        'title': f'Тег: {tag.tag}',
        'description': 'Арт-промпты с выбранным тегом.',
        'posts': posts,
        'cat_selected': None,
        'selected_tag': tag.id,
        **get_base_context(),
    }

    return render(request, 'artprompt/index.html', data)


@login_required
def idea_by_id(request, idea_id):
    idea = get_object_or_404(
        ArtPrompt.objects
        .select_related('cat', 'meta')
        .prefetch_related('tags'),
        pk=idea_id,
    )

    data = {
        'idea': idea,
        'cat_selected': idea.cat.id if idea.cat else None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/idea_id.html', data)


@login_required
def idea_by_slug(request, idea_slug):
    idea = get_object_or_404(
        ArtPrompt.objects
        .select_related('cat', 'meta')
        .prefetch_related('tags'),
        slug=idea_slug,
    )

    data = {
        'idea': idea,
        'get_params': request.GET.dict(),
        'cat_selected': idea.cat.id if idea.cat else None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/idea_slug.html', data)


@login_required
def orm_examples(request):
    first_prompt = ArtPrompt.objects.order_by('id').first()
    last_prompt = ArtPrompt.objects.order_by('id').last()
    latest_prompt = ArtPrompt.objects.latest('time_update')
    earliest_prompt = ArtPrompt.objects.earliest('time_update')

    nature_exists = ArtPrompt.objects.filter(cat__slug='nature').exists()
    nature_count = ArtPrompt.objects.filter(cat__slug='nature').count()

    q_examples = ArtPrompt.objects.filter(
        Q(style__icontains='sci') | Q(title__icontains='лес')
    )

    q_and_examples = ArtPrompt.objects.filter(
        Q(status=ArtPrompt.Status.PUBLISHED) & Q(cat__isnull=False)
    )

    q_not_examples = ArtPrompt.objects.filter(
        ~Q(style='')
    )

    f_examples = ArtPrompt.objects.filter(
        id__gt=F('cat_id')
    )

    value_examples = ArtPrompt.objects.annotate(
        source=Value('ArtPrompt project')
    ).values('title', 'style', 'source')

    full_info_examples = ArtPrompt.objects.annotate(
        full_info=Concat(
            F('title'),
            Value(' — '),
            F('style')
        )
    ).values('title', 'full_info')

    length_examples = ArtPrompt.objects.annotate(
        title_length=Length('title')
    ).values('title', 'title_length')

    aggregate_examples = ArtPrompt.objects.aggregate(
        total=Count('id'),
        avg_id=Avg('id'),
        max_id=Max('id'),
        min_id=Min('id'),
        sum_id=Sum('id'),
    )

    grouped_by_category = (
        Category.objects
        .annotate(total_prompts=Count('prompts'))
        .filter(total_prompts__gt=0)
    )

    grouped_by_tag = (
        TagPrompt.objects
        .annotate(total_prompts=Count('prompts'))
        .filter(total_prompts__gt=0)
    )

    values_examples = ArtPrompt.objects.values(
        'title',
        'cat__name',
        'style',
    )

    data = {
        'title': 'Примеры ORM-запросов',

        'first_prompt': first_prompt,
        'last_prompt': last_prompt,
        'latest_prompt': latest_prompt,
        'earliest_prompt': earliest_prompt,

        'nature_exists': nature_exists,
        'nature_count': nature_count,

        'q_examples': q_examples,
        'q_and_examples': q_and_examples,
        'q_not_examples': q_not_examples,
        'f_examples': f_examples,

        'value_examples': value_examples,
        'full_info_examples': full_info_examples,
        'length_examples': length_examples,
        'aggregate_examples': aggregate_examples,

        'grouped_by_category': grouped_by_category,
        'grouped_by_tag': grouped_by_tag,
        'values_examples': values_examples,

        'cat_selected': None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/orm_examples.html', data)


@login_required
def archive(request, year):
    if year > 2023:
        raise Http404('Архив недоступен')

    data = {
        'year': year,
        'cat_selected': None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/archive.html', data)


@login_required
def search(request):
    style = request.GET.get('style', '')
    idea_type = request.GET.get('type', '')

    data = {
        'style': style,
        'type': idea_type,
        'cat_selected': None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/search.html', data)


@login_required
def generate(request):
    data = {
        'generated': request.method == 'POST',
        'cat_selected': None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/generate.html', data)


def go_home(request):
    return redirect('home')


@login_required
def add_plain(request):
    if request.method == 'POST':
        form = AddPromptPlainForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data.copy()
            tags = data.pop('tags')

            prompt = ArtPrompt.objects.create(**data)
            prompt.tags.set(tags)

            return redirect('home')
    else:
        form = AddPromptPlainForm()

    data = {
        'title': 'Добавление арт-промпта через обычную форму',
        'form': form,
        'cat_selected': None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/add_form.html', data)


@login_required
def add_model(request):
    if request.method == 'POST':
        form = AddPromptModelForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = AddPromptModelForm()

    data = {
        'title': 'Добавление арт-промпта через ModelForm',
        'form': form,
        'cat_selected': None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/add_form.html', data)


def handle_uploaded_file(file):
    upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(file.name)
    new_name = f'{original_name.stem}_{uuid.uuid4().hex}{original_name.suffix}'
    file_path = upload_dir / new_name

    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return f'uploads/{new_name}'


@login_required
def upload_file(request):
    saved_path = None

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            saved_path = handle_uploaded_file(form.cleaned_data['file'])
    else:
        form = UploadFileForm()

    data = {
        'title': 'Загрузка файла на сервер',
        'form': form,
        'saved_path': saved_path,
        'cat_selected': None,
        'selected_tag': None,
        **get_base_context(),
    }

    return render(request, 'artprompt/upload_file.html', data)