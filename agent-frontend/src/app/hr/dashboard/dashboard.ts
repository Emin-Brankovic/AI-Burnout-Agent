import { Component, OnInit, signal, ViewChild, AfterViewInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MatPaginator, PageEvent } from '@angular/material/paginator';

export enum EmployeeStatus {
  CRITICAL = 'critical',
  MONITORING = 'monitoring',
  STABLE = 'stable',
  PENDING = 'pending'
}

export interface EmployeeData {
  initial: string;
  name: string;
  role: string;
  department: string;
  riskScore: number;
  status: string;
  statusClass: string;
  trendIcon: string;
  feedbackType: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: false,
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit, AfterViewInit {
  EmployeeStatus = EmployeeStatus;
  dashboardData = signal<any>(null);
  isLoaded = false;

  // Pagination properties
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  pageSize = 10;
  pageIndex = 0;
  totalItems = 0;
  pageSizeOptions = [5, 10, 25, 50];

  // Filter properties
  filterDepartment: string | null = null;
  filterStatus: string | null = null;
  filterTrend: string | null = null;

  // Filter options
  departments: string[] = [];
  statuses = [
    { value: 'CRITICAL', label: 'Critical' },
    { value: 'HIGH', label: 'High' },
    { value: 'MEDIUM', label: 'Medium' },
    { value: 'NORMAL', label: 'Normal' }
  ];
  trends = [
    { value: 'increasing', label: 'Increasing' },
    { value: 'stable', label: 'Stable' },
    { value: 'decreasing', label: 'Decreasing' }
  ];

  constructor(private http: HttpClient) { }

  ngOnInit(): void {
    this.loadDepartments();
    this.loadDashboardData();
  }

  ngAfterViewInit(): void {
    // Paginator is now available
  }

  loadDepartments(): void {
    // Fetch unique departments from the backend
    this.http.get<any[]>('http://localhost:8000/api/departments/').subscribe({
      next: (data) => {
        this.departments = data.map((dept: any) => dept.name);
      },
      error: (error) => {
        console.error('Error loading departments:', error);
        // Fallback to empty array if endpoint doesn't exist yet
        this.departments = [];
      }
    });
  }

  loadDashboardData(): void {
    const page = this.pageIndex + 1; // Backend uses 1-based pagination

    // Build query parameters
    let params = `page=${page}&page_size=${this.pageSize}`;

    if (this.filterDepartment) {
      params += `&department=${encodeURIComponent(this.filterDepartment)}`;
    }

    if (this.filterStatus) {
      params += `&status=${encodeURIComponent(this.filterStatus)}`;
    }

    if (this.filterTrend) {
      params += `&trend=${encodeURIComponent(this.filterTrend)}`;
    }

    this.http.get(`http://localhost:8000/api/dashboard/?${params}`).subscribe({
      next: (data: any) => {
        this.dashboardData.set(data);
        this.totalItems = data.total;
        this.isLoaded = true;
        console.log('Dashboard data loaded:', data);
      },
      error: (error) => {
        console.error('Error loading dashboard data:', error);
      }
    });
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.pageSize = event.pageSize;
    this.loadDashboardData();
  }

  onFilterChange(): void {
    // Reset to first page when filters change
    this.pageIndex = 0;
    if (this.paginator) {
      this.paginator.pageIndex = 0;
    }
    this.loadDashboardData();
  }

  clearFilters(): void {
    this.filterDepartment = null;
    this.filterStatus = null;
    this.filterTrend = null;
    this.pageIndex = 0;
    if (this.paginator) {
      this.paginator.pageIndex = 0;
    }
    this.loadDashboardData();
  }

}
