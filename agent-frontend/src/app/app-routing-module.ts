import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  { path: '', redirectTo: 'hr/dashboard', pathMatch: 'full' },
  {
    path: 'hr',
    loadChildren: () =>
      import('./hr/hr-module').then(m => m.HrModule)
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
