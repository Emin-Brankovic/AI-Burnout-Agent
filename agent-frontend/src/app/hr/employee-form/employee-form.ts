import {Component, EventEmitter, Input, OnInit, Output, signal} from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {MatSnackBar} from '@angular/material/snack-bar';
import {HttpClient} from '@angular/common/http';

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

  constructor(private fb: FormBuilder, private snackBar: MatSnackBar, private http: HttpClient) {
    this.metricsForm = this.fb.group({
      employee_id: [null, Validators.required],

      // Existing fields
      hours_worked: [8, [Validators.required, Validators.min(0), Validators.max(16)]],
      stress_level: [5, [Validators.required, Validators.min(0), Validators.max(10)]],
      hours_slept: [7, [Validators.required, Validators.min(0), Validators.max(12)]],

      // ✅ Newly added fields
      motivation_level: [5, [Validators.required, Validators.min(1), Validators.max(10)]],
      workload_intensity: [5, [Validators.required, Validators.min(1), Validators.max(10)]],
      daily_personal_time: [2, [Validators.required, Validators.min(0)]],
      overtime_hours_today: [0, [Validators.required, Validators.min(0)]],
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
    console.log(this.metricsForm.value)
    this.http.post(`http://localhost:8000/api/daily-logs/`, this.metricsForm.value).subscribe({
      next: (res: any) => {
        console.log('Employee data loaded:', res);
      },
      error: (error) => {
        console.error('Error loading dashboard data:', error);
      }
    });
  }
}
