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
        { label: 'Employees', route: '/hr/employee-form', icon: 'people' },
        { label: 'Daily Logs', route: '/hr/daily-logs', icon: 'event_note' },
        { label: 'Predictions', route: '/hr/predictions', icon: 'psychology' },
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
