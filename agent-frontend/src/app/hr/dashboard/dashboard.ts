import {Component, OnInit} from '@angular/core';
import { EmployeeStatus } from '../status-card/status-card';

@Component({
  selector: 'app-dashboard',
  standalone: false,
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {
  EmployeeStatus= EmployeeStatus;
}
