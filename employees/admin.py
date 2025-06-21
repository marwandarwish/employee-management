from .models import Employee, Attendance, Payroll, Expense
from django.contrib import admin

# Register your models here.
admin.site.register(Employee)
admin.site.register(Attendance)
admin.site.register(Payroll)
admin.site.register(Expense)
