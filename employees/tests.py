from django.test import TestCase, Client
from django.urls import reverse
from .models import Employee
from django.contrib.auth.models import User

# Create your tests here.

class EmployeeModelTest(TestCase):
    def test_create_employee(self):
        emp = Employee.objects.create(
            full_name='John Doe',
            national_id='123456789',
            mobile_phone='555-1234',
            date_of_joining='2023-01-01',
            is_active=True,
            base_salary=1000,
            variable_incentives=200
        )
        self.assertEqual(str(emp), 'John Doe')
        self.assertEqual(emp.national_id, '123456789')

class EmployeeListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
        Employee.objects.create(
            full_name='Jane Smith',
            national_id='987654321',
            mobile_phone='555-5678',
            date_of_joining='2023-02-01',
            is_active=True,
            base_salary=1200,
            variable_incentives=150
        )

    def test_employee_list_view(self):
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jane Smith')
