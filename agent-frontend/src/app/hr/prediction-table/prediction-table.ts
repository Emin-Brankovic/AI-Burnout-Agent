import {Component, OnInit} from '@angular/core';
import {HttpClient} from '@angular/common/http';

@Component({
  selector: 'app-prediction-table',
  standalone: false,
  templateUrl: './prediction-table.html',
  styleUrl: './prediction-table.css',
})


export class PredictionTable implements OnInit {
  displayedColumns: string[] = ['employee', 'department', 'riskScore', 'status', 'trend', 'feedback'];
  dataSource = ELEMENT_DATA;
  constructor(private http: HttpClient) {}
  private apiUrl = 'http://localhost:8000/api/predictions/predict';


  ngOnInit(): void {
    // this.http.post<any>(this.apiUrl, requestData).subscribe({
    //   next: (response: any) => {console.log(response);}
    // });
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

