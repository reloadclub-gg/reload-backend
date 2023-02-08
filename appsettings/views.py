import os

from django.conf import settings
from django.http.response import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string


def emails_view(request, get_context):
    context = {
        'title': 'E-mails',
        'emails': os.listdir(
            f'{settings.BASE_DIR}/accounts/templates/accounts/emails/'
        ),
        **get_context(request),
    }

    return render(request, 'emails.html', context)


def email_rendered_by_name_view(request, name):
    return JsonResponse({'email_rendered': render_to_string(f'accounts/emails/{name}')})
