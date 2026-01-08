import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
    selector: 'app-navbar',
    standalone: false,
    templateUrl: './navbar.html',
    styleUrl: './navbar.css',
})
export class Navbar {
    isMenuOpen = false;

    navItems = [
        { label: 'Dashboard', route: '/hr/dashboard', icon: 'dashboard' },
        { label: 'Daily Log Entry', route: '/hr/employee-form', icon: 'input' },
        { label: 'Daily Log Batch Entry', route: '/hr/daily-logs', icon: 'event_note' },
        { label: 'Employee Daily Log', route: '/hr/employee-logs', icon: 'assignment_ind' },
        { label: 'Reviews', route: '/hr/reviews', icon: 'rate_review' },
    ];

    constructor(private router: Router) { }

    toggleMenu(): void {
        this.isMenuOpen = !this.isMenuOpen;
    }

    isActive(route: string): boolean {
        return this.router.url === route;
    }
}
