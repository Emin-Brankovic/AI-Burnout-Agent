import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { Dashboard } from './dashboard/dashboard';
import { EmployeeForm } from './employee-form/employee-form';
import { Reviews } from './reviews/reviews';
import { DailyLogsEntryComponent } from './daily-logs-entry/daily-logs-entry';
import { EmployeeDailyLogs } from './employee-daily-logs/employee-daily-logs';

const routes: Routes = [
  // { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: Dashboard },
  { path: 'employee-form', component: EmployeeForm },
  { path: 'reviews', component: Reviews },
  { path: 'daily-logs', component: DailyLogsEntryComponent },
  { path: 'employee-logs', component: EmployeeDailyLogs },
];




@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class HrRoutingModule { }
