import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { Dashboard } from './dashboard/dashboard';
import { BurnoutRiskMonitor } from './burnout-risk-monitor/burnout-risk-monitor';
import { Header } from './header/header';
import { HrRoutingModule } from './hr-routing-module';

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

@NgModule({
  declarations: [
    Dashboard,
    BurnoutRiskMonitor,
    Header,
    StatusCard,
    PredictionTable
  ],
  imports: [
    CommonModule,
    HrRoutingModule,
    ReactiveFormsModule,
    MatIconModule,
    MatCardModule,
    MatTableModule,
    MatButtonModule,
    MatChipsModule,
    MatPaginatorModule,
    MatSelectModule,
    MatFormFieldModule,
  ]
})
export class HrModule { }
