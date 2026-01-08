import { Component, OnInit, ViewChild, AfterViewInit, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { MatTableDataSource } from '@angular/material/table';
import { MatDialog } from '@angular/material/dialog';
import { ReviewModal } from '../review-modal/review-modal';

export interface PendingReview {
    id: number;
    daily_log_id: number;
    burnout_risk: string;
    burnout_rate: number;
    confidence_score: number;
    confidence_percentage: string;
    created_at: string;
}

@Component({
    selector: 'app-reviews',
    standalone: false,
    templateUrl: './reviews.html',
    styleUrl: './reviews.css',
})
export class Reviews implements OnInit, AfterViewInit {
    displayedColumns: string[] = ['id', 'created_at', 'burnout_risk', 'confidence', 'actions'];
    dataSource = new MatTableDataSource<PendingReview>([]);
    isLoading = true;

    @ViewChild(MatPaginator) paginator!: MatPaginator;

    constructor(private http: HttpClient, private dialog: MatDialog) { }

    ngOnInit(): void {
        this.loadPendingReviews();
    }

    ngAfterViewInit() {
        this.dataSource.paginator = this.paginator;
    }

    loadPendingReviews(): void {
        this.isLoading = true;
        this.http.get<PendingReview[]>('http://localhost:8000/api/reviews/pending').subscribe({
            next: (data) => {
                this.dataSource.data = data;
                console.log(data)
                this.isLoading = false;
                // Re-assign paginator if data loads after view init
                if (this.paginator) {
                    this.dataSource.paginator = this.paginator;
                }
            },
            error: (error) => {
                console.error('Error loading pending reviews:', error);
                this.isLoading = false;
            }
        });
    }

    getStatusClass(status: string): string {
        switch (status?.toUpperCase()) {
            case 'CRITICAL': return 'status-critical';
            case 'HIGH': return 'status-high';
            case 'MEDIUM': return 'status-medium';
            case 'LOW':
            case 'NORMAL': return 'status-low';
            default: return 'status-default';
        }
    }

    reviewPrediction(element: PendingReview): void {
        this.http.get<any>(`http://localhost:8000/api/reviews/${element.id}`).subscribe({
            next: (details) => {
                // Map API response to Modal expected data
                const modalData = {
                    id: details.prediction.id,
                    log_id: details.prediction.daily_log_id,
                    work_hours: details.log_data.hours_worked,
                    stress_level: details.log_data.stress_level,
                    sleep_hours: details.log_data.hours_slept,
                    confidence: Math.round(details.confidence_score * 100),
                    predicted_risk: details.ai_prediction_type
                };

                const dialogRef = this.dialog.open(ReviewModal, {
                    width: '1200px',
                    maxWidth: '95vw', // Prevents overflow on smaller screens

                    // Set a height if you want it consistently tall
                    minHeight: '600px',
                    maxHeight: '95vh',
                    disableClose: true,
                    data: modalData
                });

                dialogRef.afterClosed().subscribe(result => {
                    if (result) {
                        this.submitReview(element.id, modalData.predicted_risk, result);
                    }
                });
            },
            error: (error) => {
                console.error('Error fetching review details:', error);
                // Optionally show an error snackbar here using MatSnackBar if available
            }
        });
    }

    submitReview(id: number, originalRisk: string, result: any): void {
        const payload = {
            is_correct: result.is_correct,
            hr_notes: result.hr_notes
        };

        this.http.post(`http://localhost:8000/api/reviews/${id}/submit`, payload).subscribe({
            next: () => {
                console.log('Review submitted successfully');
                this.loadPendingReviews(); // Refresh the table
            },
            error: (error) => {
                console.error('Error submitting review:', error);
            }
        });
    }
}
