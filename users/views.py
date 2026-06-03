import os
from django.views.generic import UpdateView
from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView
from django.core.mail import EmailMessage, get_connection
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import CreateView, TemplateView
from .forms import LoginUserForm, RegisterUserForm, UserProfileForm
from .models import Profile

class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {
        'title': 'Авторизация'
    }

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy('home')


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    extra_context = {
        'title': 'Регистрация'
    }


def logout_user(request):
    logout(request)
    return redirect('home')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'
    login_url = reverse_lazy('users:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile, created = Profile.objects.get_or_create(user=self.request.user)

        context['profile'] = profile
        context['title'] = 'Профиль пользователя'

        return context

class EditProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = UserProfileForm
    template_name = 'users/edit_profile.html'
    success_url = reverse_lazy('users:profile')
    login_url = reverse_lazy('users:login')

    def get_object(self, queryset=None):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование профиля'
        return context

class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_url = reverse_lazy('users:profile')


def env_bool(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in ('true', '1', 'yes', 'on')


def get_email_service_by_domain(email):
    domain = email.split('@')[-1].lower()

    if domain in ('mail.ru', 'bk.ru', 'inbox.ru', 'list.ru', 'internet.ru'):
        return 'MAILRU'

    if domain in ('gmail.com', 'googlemail.com'):
        return 'GMAIL'

    if domain in ('yandex.ru', 'ya.ru', 'yandex.com'):
        return 'YANDEX'

    if domain in ('outlook.com', 'hotmail.com', 'live.com'):
        return 'OUTLOOK'

    if domain in ('yahoo.com', 'yahoo.ru'):
        return 'YAHOO'

    return os.getenv('DEFAULT_EMAIL_SERVICE', 'MAILRU')


def get_email_connection_config(email):
    service = get_email_service_by_domain(email)

    host = os.getenv(f'{service}_HOST')
    port = int(os.getenv(f'{service}_PORT', 465))
    use_ssl = env_bool(f'{service}_USE_SSL', True)
    use_tls = env_bool(f'{service}_USE_TLS', False)
    username = os.getenv(f'{service}_USER')
    password = os.getenv(f'{service}_PASSWORD')

    if not host or not username or not password:
        fallback_service = os.getenv('DEFAULT_EMAIL_SERVICE', 'MAILRU')

        host = os.getenv(f'{fallback_service}_HOST')
        port = int(os.getenv(f'{fallback_service}_PORT', 465))
        use_ssl = env_bool(f'{fallback_service}_USE_SSL', True)
        use_tls = env_bool(f'{fallback_service}_USE_TLS', False)
        username = os.getenv(f'{fallback_service}_USER')
        password = os.getenv(f'{fallback_service}_PASSWORD')

    return {
        'host': host,
        'port': port,
        'use_ssl': use_ssl,
        'use_tls': use_tls,
        'username': username,
        'password': password,
    }


class AutoSMTPPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')
    extra_context = {
        'title': 'Восстановление пароля'
    }

    def form_valid(self, form):
        email = form.cleaned_data['email']
        UserModel = get_user_model()

        users = UserModel._default_manager.filter(
            email__iexact=email,
            is_active=True
        )

        for user in users:
            if not user.has_usable_password():
                continue

            smtp_config = get_email_connection_config(email)

            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=smtp_config['host'],
                port=smtp_config['port'],
                username=smtp_config['username'],
                password=smtp_config['password'],
                use_ssl=smtp_config['use_ssl'],
                use_tls=smtp_config['use_tls'],
            )

            context = {
                'email': user.email,
                'domain': self.request.get_host(),
                'site_name': 'ArtPrompt',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if self.request.is_secure() else 'http',
            }

            subject = 'Восстановление пароля ArtPrompt'
            body = render_to_string(self.email_template_name, context)

            message = EmailMessage(
                subject=subject,
                body=body,
                from_email=smtp_config['username'],
                to=[user.email],
                connection=connection,
            )

            try:
                message.send()
            except Exception as error:
                print('Не удалось отправить письмо через SMTP.')
                print(f'Причина: {error}')
                print('Для реальной отправки письма нужен пароль приложения SMTP.')
                print('Ссылка восстановления пароля была сформирована, но письмо не отправлено.')
                print(body)

        return redirect(self.get_success_url())