from django.shortcuts import render

from study.services import study_summary


def home(request):
    if not request.user.is_authenticated:
        return render(request, "core/landing.html")
    return render(request, "core/dashboard.html", {"summary": study_summary(request.user)})


def page_not_found(request, exception):
    return render(request, "404.html", status=404)


def about(request):
    return render(request, "core/about.html")
