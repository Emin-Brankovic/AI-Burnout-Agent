import { Component, Input, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-prediction-table',
  standalone: false,
  templateUrl: './prediction-table.html',
  styleUrl: './prediction-table.css',
})
export class PredictionTable implements OnInit {
  displayedColumns: string[] = ['employee', 'department', 'riskScore', 'status', 'trend', 'feedback'];
  dataSource: EmployeeData[] = [];

  @Input() set predictions(data: any[]) {
    if (data) {
      this.dataSource = data.map(item => ({
        initial: (item.name || '?').charAt(0),
        name: item.name,
        role: item.role,
        department: item.department,
        riskScore: item.risk_score,
        status: item.status,
        statusClass: this.getStatusClass(item.status),
        trendIcon: this.getTrendIcon(item.trend),
        feedbackType: item.has_feedback ? 'confirmed' : 'buttons'
      }));
    }
  }

  constructor(private http: HttpClient) { }

  ngOnInit(): void { }

  private getStatusClass(status: string): string {
    switch (status?.toUpperCase()) {
      case 'CRITICAL': return 'status-critical';
      case 'HIGH': return 'status-high';
      case 'MEDIUM': return 'status-medium';
      case 'LOW':
      case 'NORMAL': return 'status-low';
      default: return 'status-low';
    }
  }

  private getTrendIcon(trend: string): string {
    switch (trend?.toLowerCase()) {
      case 'increasing': return 'trending_up';
      case 'decreasing': return 'trending_down';
      default: return 'trending_flat';
    }
  }
}


const requestData: PredictionRequest = {
  daily_personal_time: 2,
  employee_id: 1,
  hours_slept: 7,
  hours_worked: 8.5,
  log_date: "2024-01-15T00:00:00",
  motivation_level: 7,
  overtime_hours_today: 0.5,
  stress_level: 5,
  workload_intensity: 6
};


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

const ELEMENT_DATA: EmployeeData[] = [
  {
    initial: 'J',
    name: 'John Smith',
    role: 'Senior Developer',
    department: 'Engineering',
    riskScore: 78,
    status: 'High Risk',
    statusClass: 'status-high',
    trendIcon: 'trending_up',
    feedbackType: 'buttons'
  },
  {
    initial: 'S',
    name: 'Sarah Johnson',
    role: 'Product Manager',
    department: 'Product',
    riskScore: 45,
    status: 'Medium Risk',
    statusClass: 'status-medium',
    trendIcon: 'trending_flat',
    feedbackType: 'confirmed'
  },
  {
    initial: 'M',
    name: 'Michael Chen',
    role: 'Data Analyst',
    department: 'Analytics',
    riskScore: 23,
    status: 'Low Risk',
    statusClass: 'status-low',
    trendIcon: 'trending_down',
    feedbackType: 'rejected'
  },
  {
    initial: 'E',
    name: 'Emily Rodriguez',
    role: 'UX Designer',
    department: 'Design',
    riskScore: 62,
    status: 'High Risk',
    statusClass: 'status-high',
    trendIcon: 'trending_up',
    feedbackType: 'buttons'
  },
  {
    initial: 'D',
    name: 'David Kim',
    role: 'DevOps Engineer',
    department: 'Engineering',
    riskScore: 89,
    status: 'Critical',
    statusClass: 'status-critical',
    trendIcon: 'trending_up',
    feedbackType: 'confirmed'
  }
];


export interface PredictionRequest {
  daily_personal_time: number;
  employee_id: number;
  hours_slept: number;
  hours_worked: number;
  log_date: string;
  motivation_level: number;
  overtime_hours_today: number;
  stress_level: number;
  workload_intensity: number;
}

