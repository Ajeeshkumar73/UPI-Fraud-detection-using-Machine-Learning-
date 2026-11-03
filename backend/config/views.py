from django.shortcuts import render

def landing_view(request):
    return render(request, 'landing.html')

def login_view(request):
    return render(request, 'login.html', {'is_admin_login': False})

def admin_login_view(request):
    return render(request, 'login.html', {'is_admin_login': True})

def register_view(request):
    return render(request, 'register.html')

def user_dashboard_view(request):
    return render(request, 'dashboard.html')

def send_money_view(request):
    return render(request, 'send_money.html')

def transactions_list_view(request):
    return render(request, 'transactions.html')

def transaction_detail_view(request, pk):
    return render(request, 'transaction_detail.html', {'pk': pk})

def beneficiaries_view(request):
    return render(request, 'beneficiaries.html')

def alerts_view(request):
    return render(request, 'alerts.html')

def profile_view(request):
    return render(request, 'profile.html')

def admin_dashboard_view(request):
    return render(request, 'admin_dashboard.html')

def admin_users_view(request):
    return render(request, 'admin_users.html')

def admin_transactions_view(request):
    return render(request, 'admin_transactions.html')

def admin_investigations_view(request):
    return render(request, 'admin_investigations.html')

def admin_analytics_view(request):
    return render(request, 'admin_analytics.html')

def admin_ml_model_view(request):
    return render(request, 'admin_ml_model.html')

def admin_audit_logs_view(request):
    return render(request, 'admin_audit_logs.html')
