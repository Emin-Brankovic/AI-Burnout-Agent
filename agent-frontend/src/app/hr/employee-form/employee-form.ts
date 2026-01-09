import { Component, EventEmitter, Input, OnInit, Output, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-employee-form',
  standalone: false,
  templateUrl: './employee-form.html',
  styleUrl: './employee-form.css',
})
export class EmployeeForm implements OnInit {
  // Use a Signal to manage form state
  // formState = signal({
  //   employee: '',
  //   workHours: 40,
  //   stressLevel: 5,
  //   jobSatisfaction: 5,
  //   productivity: 5,
  //   sleepHours: 7,
  //   workLifeBalance: 5
  // });
  //
  // submitCheckIn() {
  //   console.log('Submitting Wellness Check:', this.formState());
  //   // Add your API call here
  // }
  //
  // // Helper to update specific signal properties
  // updateField(field: string, value: any) {
  //   this.formState.update(state => ({ ...state, [field]: value }));
  // }
  employees: any;
  @Output() onSubmitSuccess = new EventEmitter<void>();

  metricsForm: FormGroup;
  isSubmitting = false;
  maxDate = new Date();
  minDate: Date | null = null;

  constructor(private fb: FormBuilder, private snackBar: MatSnackBar, private http: HttpClient) {
    this.metricsForm = this.fb.group({
      employee_id: [null, Validators.required],
      log_date: [new Date(), Validators.required],
      log_time: [new Date().toTimeString().slice(0, 5), Validators.required],

      // Existing fields
      hours_worked: [8, [Validators.required, Validators.min(0), Validators.max(16)]],
      stress_level: [5, [Validators.required, Validators.min(1), Validators.max(10)]],
      hours_slept: [7, [Validators.required, Validators.min(0), Validators.max(12)]],

      // ✅ Newly added fields
      motivation_level: [5, [Validators.required, Validators.min(1), Validators.max(10)]],
      workload_intensity: [5, [Validators.required, Validators.min(1), Validators.max(10)]],
      daily_personal_time: [2, [Validators.required, Validators.min(0)]],
      overtime_hours_today: [0, [Validators.required, Validators.min(0)]],
    });

    this.metricsForm.get('employee_id')?.valueChanges.subscribe(id => {
      const employee = this.employees?.find((e: any) => e.id === id);
      if (employee && employee.hire_date) {
        this.minDate = new Date(employee.hire_date);
      } else {
        this.minDate = null;
      }
    });
  }

  ngOnInit(): void {
    this.loadEmployeeData();
  }

  page = 1;
  pageSize = 10

  loadEmployeeData(): void {
    let params = `page=${this.page}&page_size=${this.pageSize}`;
    this.http.get(`http://localhost:8000/api/dashboard/?${params}`).subscribe({
      next: (data: any) => {
        console.log('Employee data loaded:', data);
        this.employees = data.employees;
      },
      error: (error) => {
        console.error('Error loading dashboard data:', error);
      }
    });
  }

  async onSubmit() {
    const formValue = { ...this.metricsForm.value };
    const date = new Date(formValue.log_date);
    const [hours, minutes] = formValue.log_time.split(':');
    date.setHours(parseInt(hours), parseInt(minutes));

    // Use the combined date-time
    formValue.log_date = date.toISOString();
    delete formValue.log_time;

    console.log(formValue)
    this.http.post(`http://localhost:8000/api/daily-logs/`, formValue).subscribe({
      next: (res: any) => {
        console.log('Employee data loaded:', res);
        this.snackBar.open(
          'Daily log submitted successfully',
          'Close',
          {
            duration: 3000,
            horizontalPosition: 'center',
            verticalPosition: 'top'
          }
        );
      },
      error: (error) => {
        console.error('Error loading dashboard data:', error);
      }
    });
  }
}
