import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Dashboard } from './dashboard/dashboard';
import { StatusCard } from './status-card/status-card';
import { BurnoutRiskMonitor } from './burnout-risk-monitor/burnout-risk-monitor';
import { Header } from './header/header';
import { HrRoutingModule } from './hr-routing-module';
import {PredictionTable} from './prediction-table/prediction-table';

import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';


@NgModule({
  declarations: [
    Dashboard,
    StatusCard,
    BurnoutRiskMonitor,
    Header,
    PredictionTable
  ],
  imports: [
    CommonModule,
    HrRoutingModule,
    MatIconModule,
    MatCardModule,
    MatTableModule,
    MatButtonModule,
    MatChipsModule,

  ]
})
export class HrModule { }
