from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator

from .models import ArtPrompt, Category, TagPrompt


def validate_russian_title(value):
    allowed_chars = (
        'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ'
        'абвгдеёжзийклмнопрстуфхцчшщьыъэюя'
        '0123456789-—,.!?() '
    )

    if not set(value) <= set(allowed_chars):
        raise ValidationError(
            'Название должно содержать только русские символы, цифры, пробелы и знаки препинания.'
        )


class AddPromptPlainForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        min_length=5,
        label='Название',
        validators=[validate_russian_title],
        widget=forms.TextInput(attrs={'class': 'form-input'}),
        error_messages={
            'required': 'Введите название арт-промпта.',
            'min_length': 'Название слишком короткое.',
        }
    )

    slug = forms.SlugField(
        max_length=255,
        label='URL',
        validators=[
            MinLengthValidator(5, message='Минимум 5 символов.'),
            MaxLengthValidator(100, message='Максимум 100 символов.'),
        ]
    )

    content = forms.CharField(
        required=False,
        label='Описание',
        widget=forms.Textarea(attrs={'cols': 60, 'rows': 6})
    )

    style = forms.CharField(
        max_length=100,
        required=False,
        label='Стиль'
    )

    status = forms.ChoiceField(
        choices=ArtPrompt.Status.choices,
        initial=ArtPrompt.Status.PUBLISHED,
        label='Статус'
    )

    cat = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label='Категория не выбрана',
        label='Категория'
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=TagPrompt.objects.all(),
        required=False,
        label='Теги',
        widget=forms.CheckboxSelectMultiple
    )


class AddPromptModelForm(forms.ModelForm):
    cat = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label='Категория не выбрана',
        label='Категория'
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=TagPrompt.objects.all(),
        required=False,
        label='Теги',
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = ArtPrompt
        fields = [
            'title',
            'slug',
            'content',
            'photo',
            'style',
            'status',
            'cat',
            'tags',
            'meta',
        ]

        labels = {
            'title': 'Название',
            'slug': 'URL',
            'content': 'Описание',
            'photo': 'Изображение',
            'style': 'Стиль',
            'status': 'Статус',
            'meta': 'Дополнительная информация',
        }

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'content': forms.Textarea(attrs={'cols': 60, 'rows': 6}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')

        if title and len(title) > 50:
            raise ValidationError('Длина названия не должна превышать 50 символов.')

        validate_russian_title(title)

        return title


class UploadFileForm(forms.Form):
    file = forms.FileField(label='Файл')