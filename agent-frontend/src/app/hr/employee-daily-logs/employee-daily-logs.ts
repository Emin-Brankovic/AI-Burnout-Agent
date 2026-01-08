import {Component, OnInit, signal, ViewChild} from '@angular/core';
import {MatPaginator, PageEvent} from '@angular/material/paginator';
import {MatSelectChange} from '@angular/material/select';
import {HttpClient} from '@angular/common/http';
import {MatTableDataSource} from '@angular/material/table';

@Component({
  selector: 'app-employee-daily-logs',
  standalone: false,
  templateUrl: './employee-daily-logs.html',
  styleUrl: './employee-daily-logs.css',
})
export class EmployeeDailyLogs implements OnInit{
  employees = signal<Employee[]>([]);
  selectedEmployeeId: number | null = null;
  displayedColumns: string[] = [
    'log_date',
    'hours_worked',
    'hours_slept',
    'stress_level',
    'motivation_level',
    'burnout_risk',
    'burnout_rate'
  ];
  dataSource = new MatTableDataSource<DailyLog>([]);
  totalLogs = 0;
  pageSize = 10;
  isLoaded = false;
  isLoading = false;

  @ViewChild(MatPaginator) paginator!: MatPaginator;

  constructor(private http: HttpClient) { }

  ngOnInit(): void {
    this.loadEmployees();
  }

  loadEmployees(): void {
    this.http.get<any>('http://localhost:8000/api/employees/').subscribe({
      next: (data) => {
        this.employees.set(data.employees);
        console.log(this.employees())
      },
      error: (err) => console.error('Error loading employees:', err)
    });
  }

  onEmployeeSelect(event: MatSelectChange): void {
    this.selectedEmployeeId = event.value;
    // Reset paginator to first page
    if (this.paginator) {
      this.paginator.pageIndex = 0;
    }
    this.loadLogs();
  }

  loadLogs(): void {
    if (!this.selectedEmployeeId) return;

    this.isLoading = true;
    const page = this.paginator ? this.paginator.pageIndex + 1 : 1;
    const size = this.paginator ? this.paginator.pageSize : this.pageSize;

    this.http.get<any>(`http://localhost:8000/api/daily-logs/employee/${this.selectedEmployeeId}?page=${page}&page_size=${size}`)
      .subscribe({
        next: (response) => {
          this.dataSource.data = response.items;
          this.totalLogs = response.total;
          this.isLoaded = true;
          this.isLoading = false;
        },
        error: (err) => {
          console.error('Error loading logs:', err);
          this.isLoading = false;
        }
      });
  }

  onPageChange(event: PageEvent): void {
    this.loadLogs();
  }

}


interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

interface DailyLog {
  id: number;
  log_date: string;
  hours_worked: number;
  hours_slept: number;
  stress_level: number;
  motivation_level: number;
  burnout_risk: string;
  burnout_rate: number;
}
