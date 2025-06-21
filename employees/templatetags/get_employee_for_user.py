from django import template
from employees.models import Employee

register = template.Library()

@register.filter
def get_employee_for_user(employees, user):
    # إذا لم يكن employees كويريست، أرجع None
    if not hasattr(employees, 'filter'):
        return None
    emp = employees.filter(national_id=user.username).first()
    if not emp:
        emp = employees.filter(full_name__iexact=user.get_full_name()).first()
    if not emp and user.email:
        emp = employees.filter(national_id=user.email).first()
    return emp 