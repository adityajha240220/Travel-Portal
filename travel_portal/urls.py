from django.contrib import admin
from django.urls import path, include
from accounts.views import LoginPageView  # ✅ Use your custom login view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth APIs (direct mapping to match Next.js proxy)
    path('api/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Root login page (at '/')
    path('', LoginPageView.as_view(), name='login'),   # ✅ Your actual login.html view

    # Planner URLs
    path('planner/', include(('planner.urls', 'planner'), namespace='planner')),  # ✅ Always start with /planner/
]