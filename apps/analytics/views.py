"""Analytics dashboard views."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.permissions import manager_required
from apps.analytics.services import (
    get_city_wide_metrics,
    get_department_performance,
    get_category_breakdown,
    get_ward_distribution
)


@login_required
@manager_required
def analytics_overview_view(request):
    """Executive analytical insights and civic performance charts."""
    metrics = get_city_wide_metrics()
    dept_performance = get_department_performance()
    category_breakdown = get_category_breakdown()
    ward_distribution = get_ward_distribution()

    return render(request, 'analytics/overview.html', {
        'metrics': metrics,
        'dept_performance': dept_performance,
        'category_breakdown': category_breakdown,
        'ward_distribution': ward_distribution,
        'title': 'Municipal Analytics & Intelligence'
    })
