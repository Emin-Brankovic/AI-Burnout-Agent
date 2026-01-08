import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { Dashboard } from './dashboard/dashboard';
import { Header } from './header/header';
import { HrRoutingModule } from './hr-routing-module';
import { SharedModule } from '../shared/shared-module';

import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { StatusCard } from './status-card/status-card';
import { PredictionTable } from './prediction-table/prediction-table';
import { EmployeeForm } from './employee-form/employee-form';
import { Reviews } from './reviews/reviews';
import { MatSlider, MatSliderThumb } from '@angular/material/slider';
import { MatProgressSpinner } from '@angular/material/progress-spinner';
import { ReviewModal } from './review-modal/review-modal';
import { DailyLogsEntryComponent } from './daily-logs-entry/daily-logs-entry';
import { MatDialogModule } from '@angular/material/dialog';
import { MatInputModule } from '@angular/material/input';
import { MatDividerModule } from '@angular/material/divider';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { FormsModule } from '@angular/forms';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { EmployeeDailyLogs } from './employee-daily-logs/employee-daily-logs';

@NgModule({
  declarations: [
    Dashboard,
    Header,
    StatusCard,
    PredictionTable,
    EmployeeForm,
    Reviews,
    ReviewModal,
    DailyLogsEntryComponent,
    EmployeeDailyLogs,
  ],
  imports: [
    CommonModule,
    HrRoutingModule,
    ReactiveFormsModule,
    FormsModule,
    SharedModule,
    MatIconModule,
    MatCardModule,
    MatTableModule,
    MatButtonModule,
    MatChipsModule,
    MatPaginatorModule,
    MatSelectModule,
    MatFormFieldModule,
    MatSlider,
    MatSliderThumb,
    MatProgressSpinner,
    MatDialogModule,
    MatInputModule,
    MatDividerModule,
    MatButtonToggleModule,
    MatSnackBarModule
  ]
})
export class HrModule { }
