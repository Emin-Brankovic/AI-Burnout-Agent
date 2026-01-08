import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { Dashboard } from './dashboard/dashboard';
import { EmployeeForm } from './employee-form/employee-form';
import { Reviews } from './reviews/reviews';
import { DailyLogsEntryComponent } from './daily-logs-entry/daily-logs-entry';

const routes: Routes = [
  // { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: Dashboard },
  { path: 'employee-form', component: EmployeeForm },
  { path: 'reviews', component: Reviews },
  { path: 'daily-logs', component: DailyLogsEntryComponent },
];




@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class HrRoutingModule { }
