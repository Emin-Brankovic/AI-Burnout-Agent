
import { Component, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MatSnackBar } from '@angular/material/snack-bar';

interface GenerateLogsRequest {
    batch_size: number;
}

interface GenerateLogsResponse {
    generated_count: number;
    requested_count: number;
    generated_logs: DailyLogResponse[];
}

interface DailyLogResponse {
    id: number;
    employee_id: number;
    log_date: string;
    hours_worked: number;
    hours_slept: number;
    daily_personal_time: number;
    motivation_level: number;
    stress_level: number;
    workload_intensity: number;
    overtime_hours_today: number;
    burnout_risk: string;
    burnout_rate: number;
    status: string;
    processed_at: string | null;
}

interface TrainResponse {
    message: string;
    model_path: string;
    metrics: {
        train_r2_score: number;
        test_r2_score: number;
        mse: number;
        mae: number;
    };
}

@Component({
    selector: 'app-daily-logs-entry',
    standalone: false,
    templateUrl: './daily-logs-entry.html',
    styleUrl: './daily-logs-entry.css',
})
export class DailyLogsEntryComponent {
    batchSize: number = 5;
    batchSizeOptions: number[] = [5, 10, 20, 50];

    dataSource = signal<DailyLogResponse[] | null>(null);
    // displayedColumns: string[] = ['id', 'employee_id', 'log_date', 'hours_worked', 'stress_level'];
    displayedColumns: string[] = [
        'id',
        'employee_id',
        'log_date',
        'hours_worked',
        'hours_slept',
        'daily_personal_time',
        'motivation_level',
        'stress_level',
        'workload_intensity',
        'overtime_hours_today'
    ];

    isLoading: boolean = false;

    constructor(private http: HttpClient, private snackBar: MatSnackBar) { }

    generateLogs(): void {
        this.isLoading = true;
        const request: GenerateLogsRequest = {
            batch_size: this.batchSize
        };

        this.http.post<GenerateLogsResponse>('http://localhost:8000/api/daily-logs/generate-random', request)
            .subscribe({
                next: (response) => {
                    this.dataSource.set(response.generated_logs)
                    this.isLoading = false;
                    this.snackBar.open(`Successfully generated ${response.generated_count} logs`, 'Close', {
                        duration: 3000,
                        panelClass: ['success-snackbar']
                    });
                },
                error: (error) => {
                    console.error('Error generating logs:', error);
                    this.isLoading = false;
                    this.snackBar.open('Failed to generate logs', 'Close', {
                        duration: 3000,
                        panelClass: ['error-snackbar']
                    });
                }
            });
    }

    trainModel(): void {
        this.isLoading = true;
        this.http.post<TrainResponse>('http://localhost:8000/api/predictions/train', {})
            .subscribe({
                next: (response) => {
                    this.isLoading = false;
                    const metrics = response.metrics;
                    const msg = `Training Complete! R²: ${metrics.test_r2_score.toFixed(3)}`;

                    this.snackBar.open(msg, 'Close', {
                        duration: 5000,
                        panelClass: ['success-snackbar']
                    });
                },
                error: (error) => {
                    console.error('Training failed:', error);
                    this.isLoading = false;
                    this.snackBar.open('Training failed: ' + (error.error?.detail || error.message), 'Close', {
                        duration: 3000,
                        panelClass: ['error-snackbar']
                    });
                }
            });
    }
}
