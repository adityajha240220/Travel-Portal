# ✅ Final corrected version of planner/urls.py
from django.urls import path
from .views import (
    PlannerPageView,
    ResultPageView,
    GeneratePlanView,
    AskQuestionView,
    LiveDealsView
)

app_name = 'planner'

urlpatterns = [
    # ✅ This makes it accessible at /planner/
    path('', PlannerPageView.as_view(), name='planner-page'),

    # Keep the rest same
    path('result-page/', ResultPageView.as_view(), name='result-page'),
    path('generate-plan/', GeneratePlanView.as_view(), name='generate-plan'),
    path('ask-question/', AskQuestionView.as_view(), name='ask-question'),
    path('live-deals/', LiveDealsView.as_view(), name='live-deals'),
]
