import {Component, Input} from '@angular/core';

@Component({
  selector: 'app-status-card',
  standalone: false,
  templateUrl: './status-card.html',
  styleUrl: './status-card.css',
})
export class StatusCard {
  @Input() status!: EmployeeStatus;
  @Input() count: number = 0;

  get statusLabel(): string {
    return this.status.charAt(0).toUpperCase() + this.status.slice(1);
  }
}
export enum EmployeeStatus {
  CRITICAL = 'critical',
  MONITORING = 'monitoring',
  STABLE = 'stable',
  PENDING = 'pending'
}
export interface StatCard {
  label: string;
  value: number;
  icon: string;
  bgClass: string;
  textClass: string;
  borderClass: string;
}
