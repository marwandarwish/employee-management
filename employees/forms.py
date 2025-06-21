from django import forms
from .models import Employee, Attendance, Payroll, Expense, ExpenseCategory

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'full_name', 'nationality', 'national_id', 'mobile_phone',
            'date_of_joining', 'work_location', 'is_active', 'base_salary', 'variable_incentives', 'profile_pic'
        ]
        labels = {
            'full_name': 'الاسم الكامل',
            'nationality': 'الجنسية',
            'national_id': 'رقم الهوية /الجواز',
            'mobile_phone': 'رقم الجوال',
            'date_of_joining': 'تاريخ التعيين',
            'work_location': 'مكان العمل',
            'is_active': 'نشط',
            'base_salary': 'الراتب الأساسي',
            'variable_incentives': 'الحوافز المتغيرة',
            'profile_pic': 'صورة الملف الشخصي',
        }
        widgets = {
            'nationality': forms.Select(attrs={'class': 'select2 form-control'}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'check_in', 'check_out', 'date', 'is_absent', 'excused_absence', 'absence_reason']
        widgets = {
            'employee': forms.Select(attrs={'class': 'select2 form-control'}),
            'check_in': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'step': 60}),
            'check_out': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'step': 60}),
        }
        labels = {
            'employee': 'الموظف',
            'check_in': 'وقت الحضور',
            'check_out': 'وقت الانصراف',
            'date': 'التاريخ',
            'is_absent': 'غائب',
            'excused_absence': 'غياب بعذر',
            'absence_reason': 'سبب الغياب',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        self.fields['check_in'].input_formats = ['%H:%M', '%I:%M %p']
        self.fields['check_out'].input_formats = ['%H:%M', '%I:%M %p']

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['employee', 'date', 'amount', 'is_salary', 'note']
        labels = {
            'employee': 'الموظف',
            'date': 'التاريخ',
            'amount': 'المبلغ',
            'is_salary': 'نوع العملية',
            'note': 'ملاحظة',
        }
        widgets = {
            'employee': forms.Select(attrs={'class': 'select2 form-control'}),
            'is_salary': forms.Select(attrs={'class': 'select2 form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class ExpenseForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.all(),
        required=False,
        label='الفئة',
        widget=forms.Select(attrs={'class': 'select2 form-control', 'data-add-url': '/expenses/categories/add/'}),
        empty_label='اختر أو أضف فئة...'
    )
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'date', 'description']
        labels = {
            'category': 'الفئة',
            'amount': 'المبلغ',
            'date': 'التاريخ',
            'description': 'الوصف',
        }
        widgets = {
            'category': forms.Select(attrs={'class': 'select2 form-control'}),
        }

class AttendanceFilterForm(forms.Form):
    FILTER_TYPE_CHOICES = [
        ('date', 'تاريخ محدد'),
        ('range', 'خلال فترة زمنية'),
    ]
    filter_type = forms.ChoiceField(
        choices=FILTER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='date',
        label='نوع الفلترة',
        required=True
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        label='الموظف',
        empty_label='الكل',
        widget=forms.Select(attrs={'class': 'select2 form-control'})
    )
    date = forms.DateField(
        required=False,
        label='تاريخ محدد',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    start_date = forms.DateField(
        required=False,
        label='من تاريخ',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        label='إلى تاريخ',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

class PayrollFilterForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        label='الموظف',
        empty_label='الكل',
        widget=forms.Select(attrs={'class': 'select2 form-control'})
    )
    start_date = forms.DateField(
        required=False,
        label='من تاريخ',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        label='إلى تاريخ',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

class ExpenseFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.all(),
        required=False,
        label='الفئة',
        empty_label='الكل',
        widget=forms.Select(attrs={'class': 'select2 form-control'})
    )
    start_date = forms.DateField(
        required=False,
        label='من تاريخ',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        label='إلى تاريخ',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    ) 