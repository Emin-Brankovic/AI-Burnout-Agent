import {Component, Inject, OnInit, signal} from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-review-modal',
  standalone: false,
  templateUrl: './review-modal.html',
  styleUrl: './review-modal.css',
})
export class ReviewModal implements OnInit {
  reviewForm: FormGroup;
  riskLevels = ['LOW', 'MEDIUM', 'HIGH'];
  displayedColumns: string[] = [
    'date',
    'hours_worked',
    'hours_slept',
    'overtime',
    'workload',
    'burnout_risk',
    'burnout_rate',
    'confidence',
    'stress',
    'motivation'
  ];
  historyData = signal<any[]>([]);

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    public dialogRef: MatDialogRef<ReviewModal>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {
    this.reviewForm = this.fb.group({
      hr_notes: ['', [Validators.required, Validators.maxLength(500)]],
      is_correct: [true, Validators.required]
    });
  }

  ngOnInit(): void {
    this.loadSubsequentLogs(this.data.log_id);
  }

  loadSubsequentLogs(logId: number) {
    this.http
      .get<any[]>(`http://localhost:8000/api/daily-logs/${logId}/subsequent`)
      .subscribe({
        next: (logs) => {
          this.historyData.set(
            logs.map(log => ({
              id: log.id,
              created_at: new Date(log.log_date),

              hours_worked: log.hours_worked,
              hours_slept: log.hours_slept,
              overtime_hours: log.overtime_hours_today,
              workload: log.workload_intensity,

              burnout_risk: log.burnout_risk,
              burnout_rate: log.burnout_rate,

              confidence: log.confidence_score
                ? Math.round(log.confidence_score * 100)
                : 0,

              stress: log.stress_level,
              motivation: log.motivation_level,

              daily_personal_time: log.daily_personal_time,
              employee_id: log.employee_id
            }))
          );
        },
        error: (err) => console.error('Failed to load subsequent logs', err)
      });
  }
  onConfirm() {
    if (this.reviewForm.valid) {
      this.dialogRef.close(this.reviewForm.value);
    }
  }
}
