from django.core.paginator import Paginator


def paginate_queryset(request, queryset, per_page):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def query_prefix(request):
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return f"{encoded}&" if encoded else ""
