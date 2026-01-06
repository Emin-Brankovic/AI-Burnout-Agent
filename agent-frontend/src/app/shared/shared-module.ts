import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatBadgeModule } from '@angular/material/badge';

import { Navbar } from './navbar/navbar';

@NgModule({
    declarations: [
        Navbar
    ],
    imports: [
        CommonModule,
        RouterModule,
        MatIconModule,
        MatButtonModule,
        MatBadgeModule,
    ],
    exports: [
        Navbar
    ]
})
export class SharedModule { }
