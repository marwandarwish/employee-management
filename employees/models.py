from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django_countries.fields import CountryField
from datetime import timedelta

class Employee(models.Model):
    full_name = models.CharField(max_length=255)
    national_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    nationality = CountryField(verbose_name="الجنسية", blank_label='(اختر الدولة)')
    mobile_phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_joining = models.DateField(verbose_name="تاريخ التعيين", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    variable_incentives = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profile_pic = models.ImageField(upload_to='', blank=True, null=True, verbose_name="الصورة الشخصية")
    work_location = models.CharField(max_length=100, verbose_name="مكان العمل", blank=True, null=True)

    def __str__(self):
        return self.full_name

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    check_in = models.DateTimeField(blank=True, null=True)
    check_out = models.DateTimeField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    is_absent = models.BooleanField(default=False, verbose_name="غائب")
    excused_absence = models.BooleanField(null=True, blank=True, verbose_name="غياب بعذر")
    absence_reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="سبب الغياب")

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"

    @property
    def late_duration(self):
        """
        Returns a timedelta of late duration if check_out > (check_in + 12 hours), else None.
        """
        if self.check_in and self.check_out:
            expected_out = self.check_in + timedelta(hours=12)
            if self.check_out > expected_out:
                return self.check_out - expected_out
        return None

    @property
    def late_duration_str(self):
        """
        Returns the late duration as a string in H:MM format, or None if no late duration.
        """
        late = self.late_duration
        if late:
            total_minutes = int(late.total_seconds() // 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}:{minutes:02d}"
        return None

    @property
    def out_difference_str(self):
        """
        Returns the difference between actual and expected check_out as a string with sign.
        Positive if extra time, negative if left early, zero if on time.
        """
        if self.check_in and self.check_out:
            expected_out = self.check_in + timedelta(hours=12)
            diff = self.check_out - expected_out
            total_minutes = int(diff.total_seconds() // 60)
            sign = '+' if total_minutes > 0 else ('-' if total_minutes < 0 else '')
            abs_minutes = abs(total_minutes)
            hours = abs_minutes // 60
            minutes = abs_minutes % 60
            if hours:
                return f"{sign}{hours}:{minutes:02d} ساعة"
            else:
                return f"{sign}{minutes} دقيقة"
        return None

class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_salary = models.BooleanField(default=True)  # True for salary, False for withdrawal
    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.amount} on {self.date}"

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="اسم الفئة")

    def __str__(self):
        return self.name

class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الفئة")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.category} - {self.amount} on {self.date}"
