from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from .models import Employee, Attendance, Payroll, Expense, ExpenseCategory
from .forms import EmployeeForm, AttendanceForm, PayrollForm, ExpenseForm, AttendanceFilterForm, PayrollFilterForm, ExpenseFilterForm
import json
from django.utils import timezone
from datetime import timedelta, date
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal

# Create your views here.

@login_required
def employee_list(request):
    employees = Employee.objects.order_by('-is_active', '-id')
    return render(request, 'employees/employee_list.html', {'employees': employees})

@permission_required('employees.add_employee', raise_exception=True)
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'form_title': 'Add Employee'})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/employee_detail.html', {'employee': employee})

@login_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form, 'form_title': 'Edit Employee'})

@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})

@login_required
def attendance_list(request):
    employees = Employee.objects.filter(is_active=True)
    attendance_records = Attendance.objects.select_related('employee').order_by('-date', '-check_in')

    filter_form = AttendanceFilterForm(request.GET or None)
    employee_id = request.GET.get('employee')
    filter_type = 'date'
    date_value = date.today()
    start_date = None
    end_date = None

    if filter_form.is_valid():
        employee = filter_form.cleaned_data.get('employee')
        filter_type = filter_form.cleaned_data.get('filter_type') or 'date'
        date_value = filter_form.cleaned_data.get('date') or date.today()
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')

        if employee:
            attendance_records = attendance_records.filter(employee=employee)
        if filter_type == 'range' and start_date and end_date:
            attendance_records = attendance_records.filter(date__range=[start_date, end_date])
        elif filter_type == 'date' and date_value:
            attendance_records = attendance_records.filter(date=date_value)

    absent_count = attendance_records.filter(is_absent=True).count()
    # مجموع وقت التأخير (صافي الفروق)
    late_total_minutes = 0
    for rec in attendance_records.filter(is_absent=False):
        if hasattr(rec, 'check_in') and hasattr(rec, 'check_out') and rec.check_in and rec.check_out:
            expected_out = rec.check_in + timedelta(hours=12)
            diff = rec.check_out - expected_out
            late_total_minutes += int(diff.total_seconds() // 60)
    # تحويل المجموع إلى ساعات ودقائق مع عرض الإشارة بشكل صحيح
    sign = '-' if late_total_minutes < 0 else ''
    abs_minutes = abs(late_total_minutes)
    late_total_hours = abs_minutes // 60
    late_total_rem_minutes = abs_minutes % 60
    # صياغة النص النهائي
    if abs_minutes >= 60:
        late_total_str = f"{sign}{late_total_hours} ساعة و{late_total_rem_minutes} دقيقة"
    else:
        late_total_str = f"{sign}{late_total_rem_minutes} دقيقة"

    return render(request, 'employees/attendance_list.html', {
        'attendance_records': attendance_records,
        'employees': employees,
        'selected_employee': employee_id,
        'selected_date': date_value,
        'filter_form': filter_form,
        'filter_type': filter_type,
        'start_date': start_date,
        'end_date': end_date,
        'absent_count': absent_count,
        'late_total_str': late_total_str,
    })

@permission_required('employees.add_attendance', raise_exception=True)
def attendance_record(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تسجيل الحضور بنجاح.")
            return redirect('attendance_list')
        else:
            messages.error(request, "حدث خطأ أثناء تسجيل الحضور. يرجى التأكد من صحة البيانات.")
    else:
        form = AttendanceForm()
    return render(request, 'employees/attendance_form.html', {'form': form})

@login_required
def payroll_list(request):
    payroll_records = Payroll.objects.select_related('employee').order_by('-date')
    filter_form = PayrollFilterForm(request.GET or None)
    if filter_form.is_valid():
        employee = filter_form.cleaned_data.get('employee')
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')
        if employee:
            payroll_records = payroll_records.filter(employee=employee)
        if start_date and end_date:
            payroll_records = payroll_records.filter(date__range=[start_date, end_date])
        elif start_date:
            payroll_records = payroll_records.filter(date__gte=start_date)
        elif end_date:
            payroll_records = payroll_records.filter(date__lte=end_date)
    # المجموع النهائي بغض النظر عن النوع
    total_received = payroll_records.aggregate(total=models.Sum('amount'))['total'] or 0
    print(f"[DEBUG] مجموع الراتب المستلم (total_received): {total_received}")
    return render(request, 'employees/payroll_list.html', {
        'payroll_records': payroll_records,
        'filter_form': filter_form,
        'total_received': total_received,
    })

@permission_required('employees.add_payroll', raise_exception=True)
def payroll_log(request):
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payroll_list')
    else:
        form = PayrollForm()
    return render(request, 'employees/payroll_form.html', {'form': form})

@login_required
def expense_list(request):
    expenses = Expense.objects.select_related('category').order_by('-date')
    filter_form = ExpenseFilterForm(request.GET or None)
    employees = Employee.objects.all()
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')
        if category:
            expenses = expenses.filter(category=category)
        if start_date and end_date:
            expenses = expenses.filter(date__range=[start_date, end_date])
        elif start_date:
            expenses = expenses.filter(date__gte=start_date)
        elif end_date:
            expenses = expenses.filter(date__lte=end_date)
    total_amount = expenses.aggregate(total=models.Sum('amount'))['total'] or 0
    return render(request, 'employees/expense_list.html', {
        'expenses': expenses,
        'filter_form': filter_form,
        'total_amount': total_amount,
        'employees': employees,
    })

@permission_required('employees.add_expense', raise_exception=True)
def expense_add(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'employees/expense_form.html', {'form': form})

@permission_required('employees.view_report', raise_exception=True)
def dashboard(request):
    # حفظ الفلترة في الجلسة
    if request.method == 'GET' and (request.GET.get('start') or request.GET.get('end')):
        request.session['dashboard_start'] = request.GET.get('start')
        request.session['dashboard_end'] = request.GET.get('end')
        request.session['dashboard_compare_start'] = request.GET.get('compare_start')
        request.session['dashboard_compare_end'] = request.GET.get('compare_end')

    # تحديد الفترة الحالية
    start_date = request.GET.get('start') or request.session.get('dashboard_start')
    end_date = request.GET.get('end') or request.session.get('dashboard_end')
    compare_start = request.GET.get('compare_start') or request.session.get('dashboard_compare_start')
    compare_end = request.GET.get('compare_end') or request.session.get('dashboard_compare_end')
    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()
    expenses = Expense.objects.select_related('category').filter(date__range=[start_date, end_date])
    payrolls = Payroll.objects.filter(date__range=[start_date, end_date])

    # فترة مقارنة (اختياري)
    compare_expenses = compare_payrolls = []
    if compare_start and compare_end:
        compare_expenses = Expense.objects.filter(date__range=[compare_start, compare_end])
        compare_payrolls = Payroll.objects.filter(date__range=[compare_start, compare_end])

    # ألوان ثابتة للفئات
    color_map = {
        'رواتب الموظفين': '#20c997',
        'كهرباء': '#ffc107',
        'إيجار': '#007bff',
        'أخرى': '#6c757d',
        'مياه': '#17a2b8',
        'صيانة': '#dc3545',
        'وقود': '#9c27b0',
        'هاتف': '#ff9800',
    }
    color_palette = list(color_map.values()) + ['#28a745', '#343a40', '#f8f9fa']

    # الفئات التي لها مصروف خلال الفترة
    categories = ExpenseCategory.objects.filter(expense__in=expenses).distinct()
    category_colors = {cat.name: color_map.get(cat.name, color_palette[i % len(color_palette)]) for i, cat in enumerate(categories)}

    # كروت: مجموع كل فئة
    cards = []
    for cat in categories:
        total = float(expenses.filter(category=cat).aggregate(total=models.Sum('amount'))['total'] or 0)
        cards.append({
            'name': cat.name,
            'total': total,
            'color': category_colors[cat.name],
        })
    # كارت الرواتب (Payroll)
    payroll_total = float(payrolls.aggregate(total=models.Sum('amount'))['total'] or 0)
    cards.insert(0, {'name': 'رواتب الموظفين', 'total': payroll_total, 'color': color_map['رواتب الموظفين']})

    # كارت إجمالي المصروفات الكلية
    total_all = sum([c['total'] for c in cards])
    cards.insert(0, {'name': 'إجمالي المصروفات', 'total': total_all, 'color': '#6f42c1'})

    # كارت أكثر فئة إنفاقاً
    max_card = max(cards[1:], key=lambda c: c['total']) if len(cards) > 1 else None

    # مقارنة بين فترتين
    compare_total = 0
    compare_payroll_total = 0
    if compare_expenses or compare_payrolls:
        compare_total = float(sum(e.amount for e in compare_expenses)) + float(sum(p.amount for p in compare_payrolls))
        compare_payroll_total = float(sum(p.amount for p in compare_payrolls))
    diff = total_all - compare_total
    diff_percent = (diff / compare_total * 100) if compare_total else 0

    # Pie chart: breakdown
    breakdown_labels = [c['name'] for c in cards[1:]]
    breakdown_data = [c['total'] for c in cards[1:]]
    breakdown_colors = [c['color'] for c in cards[1:]]

    # Bar chart: توزيع المصروفات حسب الفئة
    bar_labels = breakdown_labels
    bar_data = breakdown_data
    bar_colors = breakdown_colors

    # Time-series: إجمالي المصروفات عبر الزمن
    date_totals = {}
    for exp in expenses:
        d = exp.date.isoformat()
        date_totals[d] = date_totals.get(d, 0) + float(exp.amount)
    for p in payrolls:
        d = p.date.isoformat()
        date_totals[d] = date_totals.get(d, 0) + float(p.amount)
    time_series_labels = sorted(date_totals.keys())
    time_series_data = [date_totals[d] for d in time_series_labels]

    # نسبة الرواتب من إجمالي المصروفات
    payroll_percent = (payroll_total / total_all * 100) if total_all else 0

    # متوسط الإنفاق اليومي والشهري
    days_count = (timezone.datetime.fromisoformat(end_date) - timezone.datetime.fromisoformat(start_date)).days + 1
    daily_avg = total_all / days_count if days_count else 0
    monthly_avg = total_all / max(1, days_count/30)

    # آخر 5 عمليات مصروف/راتب
    last_expenses = list(expenses.order_by('-date')[:5])
    last_payrolls = list(payrolls.order_by('-date')[:5])
    last_operations = sorted(last_expenses + last_payrolls, key=lambda x: x.date, reverse=True)[:5]

    # بيانات التصدير (كل العمليات خلال الفترة)
    export_operations = list(expenses) + list(payrolls)

    context = {
        'cards': cards,
        'max_card': max_card,
        'compare_total': compare_total,
        'compare_payroll_total': compare_payroll_total,
        'diff': diff,
        'diff_percent': diff_percent,
        'breakdown_data': json.dumps({'labels': breakdown_labels, 'data': breakdown_data, 'colors': breakdown_colors}),
        'bar_data': json.dumps({'labels': bar_labels, 'data': bar_data, 'colors': bar_colors}),
        'time_series_labels': json.dumps(time_series_labels),
        'time_series_data': json.dumps(time_series_data),
        'payroll_percent': payroll_percent,
        'daily_avg': daily_avg,
        'monthly_avg': monthly_avg,
        'last_operations': last_operations,
        'export_operations': export_operations,
        'start_date': start_date,
        'end_date': end_date,
        'compare_start': compare_start,
        'compare_end': compare_end,
    }
    return render(request, 'employees/dashboard.html', context)

@login_required
@csrf_exempt
def expense_category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            cat, created = ExpenseCategory.objects.get_or_create(name=name)
            return JsonResponse({'id': cat.id, 'name': cat.name, 'created': created})
        return JsonResponse({'error': 'اسم الفئة مطلوب'}, status=400)
    return JsonResponse({'error': 'طريقة الطلب غير مدعومة'}, status=405)
