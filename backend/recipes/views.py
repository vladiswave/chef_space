from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404

from recipes.models import Recipe


def short_link_redirect(request, short_hash):
    recipe = get_object_or_404(Recipe, short_hash=short_hash)
    frontend_url = request.build_absolute_uri(f'/recipes/{recipe.pk}/')
    return HttpResponsePermanentRedirect(frontend_url)
