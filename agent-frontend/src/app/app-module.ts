import { NgModule, provideBrowserGlobalErrorListeners } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing-module';
import { App } from './app';
import { PredictionTable } from './prediction-table/prediction-table';

@NgModule({
  declarations: [
    App,
    PredictionTable
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,

  ],
  providers: [
    provideBrowserGlobalErrorListeners()
  ],
  bootstrap: [App]
})
export class AppModule { }
